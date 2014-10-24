import sys
import sqlalchemy as sa
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
#from sqlalchemy.ext.declarative import DeferredReflection
try:
    from sqlalchemy.ext.declarative.api import _declarative_constructor
except ImportError:
    # not >0.8
    from sqlalchemy.ext.declarative import _declarative_constructor
from sqlalchemy import event


def copy_metadata(metadata, prefix='', schema=None, metadata_out=None):
    """
    Copies tables to new metadata with new schema and/or name prefix.

    To make a new database with the result, use metadata.create_all(engine).
    
    """
    if not metadata_out:
        metadata_out = sa.MetaData()

    if schema:
        metadata_out.schema = schema
    else:
        metadata_out.schema = metadata.schema

    # assign new schema to tables
    for table in metadata.tables.values():
        table.tometadata(metadata_out, schema=schema)

    # assign prefix to tables
    for table in metadata_out.tables.values():
        table.name = prefix + table.name
        
    return metadata_out


def get_infovals(meta, structure, key):
    """
    Get flattened values from column info dictionary for given metadata and 
    desired structure.

    If key is not in column info, None is used.

    Returns
    -------
    colnames: list
        Flattened column names.
    vals: list

    Examples
    --------
    >>> from pisces.schema.kbcore import Base
    >>> fields, defaults = get_infovals(Base.metadata, ['site'], 'default')
    >>> print defaults
    ['-', -1, 2286324, -999.0, -999.0, -999.0, '-', '-', '-', -99999, -99999, <built-in method now of type object at 0x100601060>]
    >>> print fields
    ['sta', 'ondate', 'offdate', 'lat', 'lon', 'elev', 'staname', 'statype', 'refsta', 'dnorth', 'deast', 'lddate']

    """
    # TODO: make this recursive?
    # TODO: make this more efficient.

    # cache all tables
    tabledct = dict([(itable.name, itable) for itable in meta.tables.values()])
    # cache all unique column info values in metadata in a dict
    colvaldct = {}
    for t in meta.tables.values():
        for c in t.columns:
            colvaldct[c.name] = c.info.get(key, None)

    structvals = []
    colnames = []
    for i, item in enumerate(structure):
        if item in tabledct:
            itabvals = [c.info.get(key, None) for c in tabledct[item].columns]
            structvals.extend(itabvals)
            colnames.extend([c.name for c in tabledct[item].columns])
        elif item in colvaldct:
            structvals.append(colvaldct[item])
            colnames.append(item)

    return colnames, structvals

def attr_generate(cls, attr='keyvalue'):
    """
    Decorate a class that contains integer 'keyvalue' id attribute with 
    a next() integer incrementing method.

    Notes
    -----
    If your ID instance is in a session, using .next() modifies it, and thus
    stages it for updating upon the next session transaction (flush or commit).
    This is bad if it is an existing table you don't have write privileges on.

    Examples
    --------
    >>> Lastid, = pisces.get_tables(session.bind, ['lastid'])
    >>> Lastid = attr_generate(Lastid)
    >>> orid = Lastid(keyname='orid', keyvalue=1000)
    >>> orid.next()
    1001
    >>> orid.keyvalue
    1001
    >>> session.commit() #does nothing b/c orid wasn't added
    >>> orid = session.query(Lastid).filter(Lastid.keyname == 'orid').first()
    >>> orid.keyvalue
    10
    >>> orid.next()
    11
    >>> session.commit() #updates orid in the database

    """
    def next(self):
        """Set and return the next integer value of 'keyvalue'."""
        setattr(self, attr, getattr(self, attr) + 1)
        return getattr(self, attr)
    cls.next = next
    return cls


def string_formatter(meta, structure):
    """
    Get string substitution formatter for given structure and schema.
    
    If you're looking for a write_flatfile function, this is it.  It takes
    advantage of native python string formatting and file writing.

    Parameters
    ----------
    meta: sqlalchemy.MetaData 
        Columns in tables must have info={'format': ?}
    structure: iterable of str
        Strings are known schema objects (tables, columns).
        
    Returns
    -------
    fmt: str
        String substitution formatter for provided structure within provided
        schema.
    
    Examples
    --------
    >>> recs = session.query(Origin, sta.lat, sta.lon).limit(10).all()
    >>> fmt = string_formatter(meta.tables.values(), ['origin', 'lat', 'lon'])
    >>> with open('origin_lat_lon.txt', 'w') as f:
            for rec in recs:
                f.write(fmt.format(rec))
    
    """
    # TODO: rewrite to use get_infovals
    # XXX: fails with some structures
    # o = session.query(Origin).first()
    # string_formatter(KBBase.metadata, ['lat','lon']).format(o) # fails
    # o = session.query(Origin.lat, Origin.lon).first()
    # string_formatter(KBBase.metadata, ['lat','lon']).format(o) # succeeds
    tabledct = dict([(itable.name, itable) for itable in meta.tables.values()])
    colfmtdct = {}
    for t in meta.tables.values():
        for c in t.columns:
            colfmtdct[c.name] = c.info.get('format', None)
    structfmt = []
    for idx, item in enumerate(structure):
        if item in tabledct:
            itabfmt = ' '.join(["{{{}.{}:{}}}".format(idx, c.name, c.info.get('format','')) for c in tabledct[item].columns])
            structfmt.append(itabfmt)
        elif item in colfmtdct:
            structfmt.append("{{{}:{}}}".format(idx, colfmtdct[item]))
    return ' '.join(structfmt)

## Methods for PiscesMeta ##
def _init(self, *args, **kwargs):
    """
    Create a mapped table instance (a row).

    Constructor accepts all correctly-ordered positional arguments for a table as a
    sequence OR a subset of known keyword arguments.  None values replaced with 
    __table__ column info['default'] value.

    """
    # TODO: cache hidden properties line _positions, _types, _defaults, ...
    #    in get_tables?
    # XXX: fails if no column.info dictionary (schema=Base.metadata wasn't
    #   supplied).
    # XXX: perhaps None was the intended value
    # change init to accept any kwargs, but ignore unknown ones.
    if args:
        if kwargs:
            raise ValueError("Either positional or keyword arguments accepted.")
        if len(args) != len(self.__table__.columns):
            raise ValueError("Provide a position argument for each column.")
        for c, ival in zip(self.__table__.columns, args):
            dflt = c.info.get('default', None)
            if ival is None:
                if hasattr(dflt, '__call__'):
                    #handle callables, like datetime.datetime.now
                    setattr(self, c.name, dflt())
                else:
                    setattr(self, c.name, dflt)
            else:
                setattr(self, c.name, ival)
    else:
        # use SQLA's keyword constructor, then replace Nones with values
        _declarative_constructor(self, **kwargs)
        for c, ival in [(col, getattr(self, col.name, None)) 
                        for col in self.__table__.columns]:
            dflt = c.info.get('default', None)
            if ival is None:
                if hasattr(dflt, '__call__'):
                    setattr(self, c.name, dflt())
                else:
                    setattr(self, c.name, dflt)


def _str(self):
    """Return a schema-aware flat file row representation."""
    fmt = string_formatter(self.__table__.metadata, [self.__table__.name])

    return fmt.format(self)
    
def _repr(self):
    # TODO: make this use the same mechanics as __getitem__
    """
    This class can be used by ``declarative_base``, to add an automatic
    ``__repr__`` method to *all* subclasses of ``Base``. This ``__repr__`` 
    will represent values as::
 
        ClassName(pkey_1=value_1, pkey_2=value_2, ..., pkey_n=value_n)
 
    where ``pkey_1..pkey_n`` are the primary key columns of the mapped table
    with the corresponding values.
    
    Notes
    -----
    Stolen and modified from http://foobar.lu/wp/2013/07 .

    """
    # doesn't work for children of DeferredReflection
    items = [(col.name, getattr(self, col.name)) for col in 
              self.__mapper__.primary_key]

    return "{0}({1})".format(self.__class__.__name__,
        ', '.join(['{0}={1!r}'.format(*_) for _ in items]))


def from_string(cls, line, default_on_error=None):
    """
    Construct a mapped table instance from correctly formatted flat file line.

    Works with fixed-length fields, separated by a single whitespace.

    Parameters
    ----------
    line: str
        Flat file line (best to remove newline, but maybe not a problem).
    default_on_error: list, optional
        Supply a list of column names that return default values if they
        produce an error during parsing (e.g. lddate).

    Raises
    ------
    ValueError:  Can't properly parse the line.


    Notes
    -----
    default_on_error is useful for malformed fields, but it will also mask
    other problems with line parsing. It's better to pre-process tables 
    to match the table specifications or catch exceptions and isolate 
    these lines.  
        
    Examples
    --------
    >>> with open('TA.site','r') as ffsite:
            for line in ffsite:
                isite = Site.from_string(line)
    or
    >>> with open('TA.site','r') as ffsite:
            for line in ffsite:
                isite = Site.from_string(line, default_on_error=['lddate'])

    """
    # TODO: use some sort of cached generator expression at load time for this?
    # TODO: check line length before proceeding.
    # TODO: write this as a separate importable function, and just wrap it here?
    vals = []
    pos = 0
    for col, w, parser in [(c.name, c.info['width'], c.info['parse']) for c in cls.__table__.columns]:
        try:
            val = parser(line[pos:pos+w])
            #print "{} '{}'".format(col, line[pos:pos+w])
        except ValueError as e:
            #XXX: ValueError? any error?
            # remove this clause, in favor or error handling inside info['parse']
            if default_on_error and col in default_on_error:
                # None are converted to defaults during __init__
                # XXX: no it doesn't.  that'd be nice, though.
                val = None
                #val = c.info['default']
            else:
                msg = ", column {}: '{}', positions [{}:{}]".format(col, line[pos:pos+w], pos, pos+w)
                #XXX: breaks for Python 3
                raise type(e)(str(e) + msg)

                #print("column: {}, value '{}'".format(c.name, line[pos:pos+w]))
                #raise e
        vals.append(val)
        pos += w+1

    return cls(*vals)

def _getitem(self, i):
    # this makes class instances behave like NumPy records
    # implements __iter__ behavior as a side-effect
    return [getattr(self, c.name, c.info.get('default', None)) \
            for c in self.__table__.columns].__getitem__(i)

def _setitem(self, i, val):
    # this makes tables behave like NumPy records
    setattr(self, self.__table__.columns.keys()[i], val)

def _len(self):
    # needed for _getitem__, i think
    return len(self.__table__.columns)

def _eq(self):
    """ True if primary key values are all equal. """
    return all([getattr(self, c.name) == getattr(inst, c.name ) 
                for attr in self.__table__.primary_key.columns])

def _update_schema(targs, schema):
    """Put schema dict into __table_args__[-1].

    Parameters
    ----------
    targs: tuple
        The initial __table_args__.
    schema: str
        The schema string for __table_args__[-1]['schema'].

    Returns
    -------
    targsout : tuple
        Ends in a dict containing {'schema': schema}
        Retains all other args.

    """
    # TODO: make this a generic '_update_args' function, so it can also be used 
    #   with __mapper_args__
    try:
        # targs is a tuple ending in a dict
        targs[-1].update({'schema': schema})
    except AttributeError:
        # targs is a tuple not ending in a dict
            targs = targs + ({'schema': schema},)
    except IndexError:
        # targs is an empty tuple
            targs = ({'schema': schema},)
    except KeyError:
        # targs is a dict
        targs.update({'schema': schema})

    return targs


class PiscesMeta(DeclarativeMeta):
    def __new__(cls, clsname, parents, dct):
        #if '__abstract__' in dct:
        #    # let normal abstract construction apply.
        #    # necessary?
        #    pass
        #else:
        #    # assign methods for child classes
        dct['__init__'] = _init
        dct['__str__'] = _str
        dct['__repr__'] = _repr
        dct['__getitem__'] = _getitem
        dct['__setitem__'] = _setitem
        dct['__len__'] = _len
        dct['__eq__'] = _eq
        dct['from_string'] = classmethod(from_string)
        dct['_column_info_registry'] = {}

        # put schema into __table_args__, if present
        # see http://www.sqlalchemy.org/trac/ticket/2700 for a possibly
        #   better way to do this type of thing.
        try:
            # schema-qualified __tablename__
            schema, tablename = dct['__tablename__'].split('.')
            dct['__tablename__'] = tablename
            #ipdb.set_trace()
            # add a new base in front, with the correct schema
            SchemaBase = declarative_base(metadata=sa.MetaData(schema=schema))
            # copy the column registry into the new base, for DeferredReflection
            for p in parents:
                if getattr(p, '_column_info_registry', {}):
                    SchemaBase._column_info_registry = p._column_info_registry
            parents = (SchemaBase,) + parents
            #dct['__table_args__'] = _update_schema(dct['__table_args__'], schema)
            #dct['__table_args__'] = _update_schema(dct.get('__table_args__', ()), schema)
            #dct['__table_args__'][-1].update({'extend_existing': True})
        except KeyError:
            # no __tablename__, __table_args__
            pass
        except ValueError:
            # not schema-qualified
            pass

        return super(PiscesMeta, cls).__new__(cls, clsname, parents, dct) 
        #return DeclarativeMeta.__new__(cls, clsname, parents, dct) 
        #return type.__new__(cls, clsname, parents, dct) 

    def __init__(cls, clsname, parents, dct):
        super(PiscesMeta, cls).__init__(clsname, parents, dct) 
        # store Column info dictionary in base._column_info_registry
        for key, val in dct.iteritems():
            if isinstance(val, sa.Column):
                try:
                    cls.__base__.__dict__['_column_info_registry'][key] = val.info
                except KeyError:
                    pass


# common parser functions for info['parser']
# these return None upon exception, which is later converted to info['default']
def parse_str(s):
    return str(s).strip() or None

def parse_utf(s):
    """ Decode a utf-8 encoded string. """
    return s.strip().decode('utf-8') or None

def parse_float(s):
    return float(s) or None

def parse_int(s):
    return int(s) or None


#@event.listens_for(DeferredReflection, "instrument_class", propagate=True)
#def process_primary_keys(mapper, cls):
#    """Enforce __primary_keys__.
#
#    Overwrites cls.__mapper_args__ with a PrimaryKeyConstraint for all columns
#    named in cls.__primary_keys__.
#
#    """
#    #print " Table: {}".format(repr(t))
#    #print " __table_args__: {}".format(cls.__table_args__)
#    if hasattr(cls, '__primary_keys__'):
#        t = cls.__table__
#        if not all([key in t.primary_key.columns for key in cls.__primary_keys__]):
#            pkcols = [getattr(t.c, col) for col in cls.__primary_keys__]
#            #pk = sa.PrimaryKeyConstraint(*pkcols)
#            #pk = sa.PrimaryKeyConstraint(*cls.__primary_keys__)
#            #cls.__table_args__ = (pk,) + cls.__table_args__
#            #cls.__mapper_args__ = (pk,)
#            cls.__mapper_args__ = (sa.PrimaryKeyConstraint(*pkcols),)
#            # XXX: I don't know why the dictionary syntax doesn't work.
#            #cls.__mapper_args__ = {'primary_key': pkcols}
#
#    # update __table__.columns with info dictionaries in base._column_info_registry
#    column_info = getattr(cls.__base__, '_column_info_registry', None)
#    if column_info:
#        for c in cls.__table__.columns:
#            c.info.update(column_info.get(c.name, {}))
#
