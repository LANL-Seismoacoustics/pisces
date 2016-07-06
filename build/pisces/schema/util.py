from collections import namedtuple

import sqlalchemy as sa
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
try:
    from sqlalchemy.ext.declarative.api import _declarative_constructor
except ImportError:
    # not >0.8
    from sqlalchemy.ext.declarative import _declarative_constructor

# NO SELF IMPORTS!

# TODO: add a .to_dict() method or a dict-like __getitem__/__setitem__, and
#   remove value iteration, so that copying a row looks like
#   Class(inst.to_dict())
#   or
#   Class(**inst)
#   and this works:
#   for (col, val) in inst:
#       print col, val
#
#   This will affect .from_string (i think) and __init__, and _print_format,
#   and __str__
# TODO: add a decorator like
#   https://blogs.gnome.org/danni/2013/03/07/generating-json-from-sqlalchemy-objects/

CoreTable = namedtuple('CoreTable', ['name', 'prototype', 'table'])

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
            #e.g. {0.attribute_name:format} {1.attribute_name:format} ...
            itabfmt = ' '.join(["{{{}.{}:{}}}".format(idx, c.name, c.info.get('format','')) \
                                for c in tabledct[item].columns])
            structfmt.append(itabfmt)
        elif item in colfmtdct:
            # e.g. {0:format} {1:format}
            structfmt.append("{{{}:{}}}".format(idx, colfmtdct[item]))
    return ' '.join(structfmt)

################ Methods for PiscesMeta #####################
def _init(self, *args, **kwargs):
    """
    Create a mapped table instance (a row).

    Constructor accepts all correctly-ordered positional arguments for a table as a
    sequence OR a subset of known keyword arguments.  None values replaced with 
    __table__ column info['default'] value.

    """
    # Given to the metaclass to become the __init__ for the class, which means things in it are 
    # done to the instances (self).

    # this method is a hot mess:
    # TODO: cache hidden properties line _positions, _types, _defaults, ...
    #    in get_tables?  --> No, put this in PiscesMeta.__init__
    # XXX: fails if no column.info dictionary (schema=Base.metadata wasn't
    #   supplied).
    # XXX: perhaps None was the intended value
    # TODO: change init to accept any kwargs, but ignore unknown ones.

    # XXX: fails for attribute name different from column name (e.g. 'yield_' vs 'yield')
    # use self.__mapper__.columns['yield_'].name to get attr-column mapping
    # TODO: I think it want this snippet to be in PiscesMeta.__new__
    #self._attrname = {c.name: a for a,c in self.__mapper__.c.items()} #{col_name: attr_name}
    #self._strfmt = string_formatter(self.__base__.metadata, [self.__table__.name])
    if args:
        # positional value instantiation
        if kwargs:
            raise ValueError("Either positional or keyword arguments accepted.")
        if len(args) != len(self.__table__.columns):
            raise ValueError("Provide a position argument for each column.")
        for c, ival in zip(self.__table__.columns, args):
            dflt = c.info.get('default', None)
            if ival is None:
                if hasattr(dflt, '__call__'):
                    # handle callables, like datetime.datetime.now
                    setattr(self, self._attrname[c.name], dflt())
                else:
                    setattr(self, self._attrname[c.name], dflt)
            else:
                setattr(self, self._attrname[c.name], ival)
    else:
        # keyword value instantiation
        # use SQLA's keyword constructor, then replace None attribute values with defaults 
        _declarative_constructor(self, **kwargs)
        for c, ival in [(col, getattr(self, self._attrname[col.name], None)) for col in self.__table__.columns]:
            dflt = c.info.get('default', None)
            if ival is None:
                if hasattr(dflt, '__call__'):
                    setattr(self, self._attrname[c.name], dflt())
                else:
                    setattr(self, self._attrname[c.name], dflt)


def _str(self):
    """Return a schema-aware flat file row representation."""
    #fmt = string_formatter(self.__table__.metadata, [attrname[c.name] for c in self.__table__.columns])
    #fmt = string_formatter(self.__table__.metadata, [self.__table__.name])
    #return fmt.format(self)
    
    # XXX: i don't know why this works.  I expected an unpacked `self` to work, because it can 
    # iterate itself.  Think it has something to do with the way _format_string is constructed.
    return self._format_string.format(*self)

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

    return "{0}({1})".format(self.__class__.__name__, ', '.join(['{0}={1!r}'.format(*_) for _ in items]))


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
            #TODO: remove this clause, in favor or error handling inside info['parse']
            if default_on_error and col in default_on_error:
                # None are converted to defaults during __init__
                # XXX: no it doesn't.  that'd be nice, though.
                val = None
                #val = c.info['default']
            else:
                msg = ", column {}: '{}', positions [{}:{}]".format(col, line[pos:pos+w], pos, pos+w)
                #XXX: breaks for Python 3
                raise type(e)(str(e) + msg)

                # debuggin
                #print("column: {}, value '{}'".format(c.name, line[pos:pos+w]))
                #raise e

        vals.append(val)
        pos += w+1

    return cls(*vals)

def _getitem(self, i):
    # integer indexing based on column order in __table__
    # helps implement __iter__ behavior as a side-effect
    values = [getattr(self, self._attrname[c.name], c.info.get('default', None)) \
            for c in self.__table__.columns]
    return values.__getitem__(i)

def _setitem(self, i, val):
    # integer indexing based on column order in __table__
    # helps implement __iter__ behavior as a side-effect
    colname = self.__table__.columns.keys()[i]
    setattr(self, self._attrname[colname], val)

def _len(self):
    # needed for _getitem__, i think
    return len(self.__table__.columns)

def _eq(self, other):
    """ True if primary key values are all equal. """
    return all([getattr(self, self._attrname[c.name]) == getattr(other, other._attrname[c.name]) 
                for c in self.__table__.primary_key.columns])


def _update_docstring(cls):
    s = '\n'.join(["{} ({}) : {!r}\n    {}".format(c.name, c.key, c.type, c.doc or 'No docstring.') \
            for c in cls.__table__.columns])
    s += "\n\nFORMAT STRING:\n{}\n".format(cls._format_string)
    s += "\n\nSQL CREATE STATEMENT:\n{}\n".format(sa.schema.CreateTable(cls.__table__))
    return s

class PiscesMeta(DeclarativeMeta):
    def __new__(cls, clsname, parents, dct):

        # child classes will have methods/data put into "dct"
        dct['__init__'] = _init
        dct['__str__'] = _str
        dct['__repr__'] = _repr
        dct['__getitem__'] = _getitem
        dct['__setitem__'] = _setitem
        dct['__len__'] = _len
        dct['__eq__'] = _eq

        dct['from_string'] = classmethod(from_string)

        dct['_column_info_registry'] = {}   #this is a class-level attribute

        # if __tablename__ looks like 'schema.tablename', split it and move schema to __table_args__
        # see http://www.sqlalchemy.org/trac/ticket/2700 for a possibly
        # better way to do this type of thing.
        try:
            schema, tablename = dct['__tablename__'].split('.')
            dct['__tablename__'] = tablename
            SchemaBase = declarative_base(metadata=sa.MetaData(schema=schema))
            # copy the column registry into the new base, for use with DeferredReflection
            for p in parents:
                if getattr(p, '_column_info_registry', {}):
                    SchemaBase._column_info_registry = p._column_info_registry
            parents = (SchemaBase,) + parents
        except KeyError:
            # no __tablename__, __table_args__
            pass
        except ValueError:
            # not a schema-qualified name
            pass

        return super(PiscesMeta, cls).__new__(cls, clsname, parents, dct) 

    def __init__(cls, clsname, parents, dct):

        # called once with a new Base
        # called again for each __abstract__ inheriting class
        # called again for each actual class
        # _not_ called for class instances (rows).  The's dct['__init__']

        # this is SQLA's DeclarativeMeta.__init__
        super(PiscesMeta, cls).__init__(clsname, parents, dct) 

        # store Column info dictionary in base._column_info_registry
        for key, val in dct.iteritems():
            if isinstance(val, sa.Column):
                try:
                    cls.__base__.__dict__['_column_info_registry'][key] = val.info
                except KeyError:
                    pass

        # for actual ORM classes, add usefull class attributes
        # "cls._attrname" is a dictionary that gives attribute name for _attrname['column name']
        if hasattr(cls, '__table__'):
            cls._attrname = {c.name: a for a,c in cls.__mapper__.c.items()} #{col_name: attr_name}
            cls._format_string = string_formatter(cls.__base__.metadata, [c.name for c in cls.__table__.columns])
            cls.__doc__ = _update_docstring(cls)


################# common parser functions for info['parser'] ##################
# these return None upon exception, which is later converted to info['default']

def parse_str(s):
    return str(s).strip() or None

def parse_utf(s):
    """ Decode a utf-8 encoded string. """
    return s.strip().decode('utf-8') or None

def parse_float(s):
    return float(s) or None

def parse_int(s):
    # XXX: int('0') will fail
    return int(s)


