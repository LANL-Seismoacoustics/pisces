# -*- coding: utf-8 -*-
"""
Common Pisces utility functions.

"""
import logging
import math
from getpass import getpass
import warnings
import functools
import inspect
import traceback
from importlib import import_module

import numpy as np
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm.exc import UnmappedInstanceError

import obspy.geodetics as geod
from obspy.core import AttribDict
from obspy.taup import TauPyModel

from pisces.schema.util import PiscesMeta


def deprecated(message: str = ''):
    """
    This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used first time and filter is set for show DeprecationWarning.
    """
    # https://stackoverflow.com/a/40899499/745557
    def decorator_wrapper(func):
        @functools.wraps(func)
        def function_wrapper(*args, **kwargs):
            current_call_source = '|'.join(traceback.format_stack(inspect.currentframe()))
            if current_call_source not in function_wrapper.last_call_source:
                warnings.warn("Function {} is now deprecated! {}".format(func.__name__, message),
                              category=DeprecationWarning, stacklevel=2)
                function_wrapper.last_call_source.add(current_call_source)

            return func(*args, **kwargs)

        function_wrapper.last_call_source = set()

        return function_wrapper
    return decorator_wrapper


TURNOFFWARNINGSMSG = """Warnings can be turned off with:
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning
"""

def db_connect(*args, **kwargs):
    """
    Connect to your database.

    Parameters
    ----------
    backend : string
        One of the SQLAlchemy connection strings from
        http://docs.sqlalchemy.org/en/rel_0_7/core/engines.html#database-urls
    user : string, optional
        Not required for sqlite.
    passwd : string, optional
        Not needed for sqlite. Prompted if needed and not provided.
    server : string, optional
        Database host server.
    port : string or integer, optional
        Port on remote server.
    instance : string, optional
        The database instance.  For sqlite, this is the file name.
    conn : string, optional
        A fully-formed SQLAlchemy style connection string.

    Returns
    -------
    session : bound SQLAlchemy Session instance

    Examples
    --------
    1. Connect to a local sqlite database file:

    >>> meta, session = db_connect(conn='sqlite:///mydb.sqlite')
    #or
    >>> meta, session = db_connect(backend='sqlite', instance='mydb.sqlite')

    Notes
    -----
    For connection string format, see:
    http://docs.sqlalchemy.org/en/rel_0_8/core/engines.html

    """
    #TODO: take advantage of sqlalchemy.engine.url.URL
    #XXX: is not protected against using args and kwargs
    if len(args) == 1:
        kwargs['conn'] = args[0]

    if kwargs.get('conn'):
        conn = kwargs.get('conn')
    else:
        backend = kwargs.get('backend')
        user = kwargs.get('user', '')
        psswd = kwargs.get('passwd', '')
        server = kwargs.get('server', '')
        port = kwargs.get('port', '')
        instance = kwargs.get('instance', '')

        if backend == 'sqlite':
            userpsswd = ''
        else:
            if user and not psswd:
                psswd = getpass("Enter password for {0}: ".format(user))
                userpsswd = ':'.join([user, psswd])
            elif psswd and not user:
                user = getpass("Enter username for given password: ")
                userpsswd = ':'.join([user, psswd])
            elif user and psswd:
                userpsswd = ':'.join([user, psswd])
            else:
                userpsswd = ':'

        if server:
            serverport = '@' + server
            if port:
                serverport += ':' + str(port)
        else:
            serverport = ''

        conn = "{0}://{1}{2}/{3}".format(backend, userpsswd, serverport, instance)

    engine = sa.create_engine(conn)
    session = Session(bind=engine)

    return session

# TODO: get rid of two different ways to connect to databases
def url_connect(url):
    """
    Connect to a database using an RFC-1738 compliant URL, like sqlalchemy's
    create_engine, prompting for a password if a username is supplied.

    Parameters
    ----------
    url : string
        A fully-formed SQLAlchemy style connection string.
        See http://docs.sqlalchemy.org/en/latest/core/engines.html#database-urls

    Returns
    -------
    session : bound SQLAlchemy Session instance

    Examples
    --------
    SQLite database file, local:
    >>> url_connect('sqlite:///local/path/to/mydb.sqlite')

    SQLite database file, full path:
    >>> url_connect('sqlite:////full/path/to/mydb.sqlite')

    Remote Oracle, OS-authenticated (no user or password needs to be specified)
    >>> url_connect('oracle://dbserver.lanl.gov:8080/mydb')

    Remote Oracle, password-authenticated (specify user, prompted for password)
    >>> url_connect('oracle://scott@dbserver.lanl.gov:8080/mydb')
    Enter password for scott:

    Remote Oracle, password-authenticated (password specified)
    >>> url_connect('oracle://scott:tiger@dbserver.lanl.gov:8080/mydb')

    """
    this_url = sa.engine.url.make_url(url)
    if this_url.username and not this_url.password:
        this_url.password = getpass("Enter password for {0}: ".format(this_url.username))

    e = sa.create_engine(this_url)

    session = Session(bind=e)

    return session

# TODO: rename this to "load_table", and make it work on a single table
@deprecated('This will be load_tables in pisces.crud in next version. ' + TURNOFFWARNINGSMSG)
def get_tables(bind, fulltablenames, metadata=None, primary_keys=None,
               base=None):
    """
    Reflect/load an arbitrary database table as a mapped class.

    This is a shortcut for SQLAlchemy's declarative mapping using __table__.
    See http://docs.sqlalchemy.org/en/rel_0_9/orm/extensions/declarative.html#using-a-hybrid-approach-with-table.

    Parameters
    ----------
    bind : sqlalchemy.engine.base.Engine instance
        Engine pointing to the target database.
    fulltables : list of strings
        Of the form ['owner1.tablename1', 'owner2.tablename2', ...]
        Leave out 'owner.' if database doesn't use owners (sqlite, etc...)
    metadata : sqlalchemy.MetaData, optional
        MetaData into which reflected Tables go. If not supplied, a new one
        is created, accessible from MyTable.metadata on one of the loaded
        tables.
    primary_keys : dict, optional
        Tablename, primary key list pairs of the form,
        {'owner1.tablename1': ['primary_key1', 'primary_key2']}
        These are required if the table is a view or has no primary key.
    base : sqlalchemy.ext.declarative.api.DeclarativeMeta, optional
        The declarative base the from which loaded table classes will inherit.
        The info dictionary of loaded Columns will be updated from those in
        the base.  These are used to generate default values and string
        representations.  Import from pisces.schema.css3, or extensions thereof.
        Default, sqlalchemy.ext.declarative.api.DeclarativeMeta.

    Returns
    -------
    list
        Corresponding list of ORM table classes mapped to reflected tables,
        Can be used for querying or making row instances.

    Raises
    ------
    sqlalchemy.exc.NoSuchTableError : Table doesn't exist.
    sqlalchemy.exc.InvalidRequestError : Table already loaded in metadata.
    sqlalchemy.exc.ArgumentError : Table has no primary key(s).

    Notes
    -----
    In SQLAlchemy, a database account/owner is generally used with the "schema"
    keyword argument.

    For core tables in a Pisces schema, this function isn't recommended.
    Instead, subclass from the known abstract table.

    Examples
    --------
    # for unknown table
    >>> import pisces.schema.css3 as css
    >>> RandomTable = get_tables(engine, ['randomtable'])

    # for a known/prototype table
    >>> class Site(css.Site):
            __tablename__ = 'myaccount.my_site_tablename'

    """
    if not metadata:
        metadata = sa.MetaData()
        if not bind:
            raise ValueError("Must provide bound metadata or bind.")
    # we have metadata
    if not bind:
        bind = metadata.bind

    ORMBase = base if base else declarative_base(metaclass=PiscesMeta,
                                                 constructor=None,
                                                 metadata=metadata)
    colinfo = getattr(base, '_column_info_registry', {})
    parents = (ORMBase,)


    outTables = []
    for fulltable in fulltablenames:
        try:
            owner, tablename = fulltable.split('.')
        except ValueError:
            # no owner given
            owner, tablename = None, fulltable

        # reflect the table
        itable = sa.Table(tablename, metadata, autoload=True,
                          autoload_with=bind, schema=owner)

        # update reflected table with known schema column info
        if colinfo:
            for col in itable.columns:
                col.info.update(colinfo.get(col.name, {}))

        dct = {'__table__': itable}
        # put any desired __table_args__: {} here

        # no primary key, can't map. spoof primary key mapping from inputs
        if primary_keys and fulltable in primary_keys:
            dct['__mapper_args__'] = {'primary_key': [getattr(itable.c, key) for key in primary_keys[fulltable]]}

        ORMTable = type(tablename.capitalize(), parents, dct)

        outTables.append(ORMTable)

    return outTables


# TODO: merge get_tables and make_tables?
@deprecated('This will be moved to pisces.crud in next version .' + TURNOFFWARNINGSMSG)
def make_table(fulltablename, prototype):
    """
    Create a new ORM class/model on-the-fly from a prototype.

    Parameters
    ----------
    fulltablename : str
        Schema-qualified name of the database table, like 'owner.tablename'
        or just 'tablename'.  The resulting classname will be the capitalized
        tablename, like 'Tablename'.
    prototype : sqlalchemy abstract ORM class
        The prototype table class. pisces.schema.css.Site, for example.

    Notes
    -----
    It's better to declare classes in an external module, and import them.
    SQLAlchemy doesn't let you use the same table names twice, so on-the-fly
    class creation and naming is risky:

    1. You can't use make_tables again if you accidentally overwrite the
       variable you used to hold the class you created.
    2. You can't use make_tables again if you import something from a
       script/module where make_tables was used with the same table name.

    """
    try:
        owner, tablename = fulltablename.split('.')
    except ValueError:
        owner, tablename = None, fulltablename

    parents = (prototype,)
    if owner:
        OwnerBase = declarative_base(metadata=sa.MetaData(schema=owner))
        parents = (OwnerBase, prototype)
    else:
        parents = (prototype,)

    dct = {'__tablename__': tablename}

    return type(tablename.capitalize(), parents, dct)


def make_same_size(lat1, lon1, lat2, lon2):
    """
    Returns numpy arrays the same size as longest inputs.
    assume: lat1/lon1 are same size and lat2/lon2 are same size
    assume: the smaller of the sizes is a scalar

    """
    #TODO: EAFP
    lon1 = np.array(lon1)
    lat1 = np.array(lat1)
    lon2 = np.array(lon2)
    lat2 = np.array(lat2)
    #assume: lat1/lon1 are same size and lat2/lon2 are same size
    #assume: the smaller of the sizes is a scalar
    N1 = lon1.size
    N2 = lon2.size
    if N1 > N2:
        lon2 = lon2.repeat(N1)
        lat2 = lat2.repeat(N1)
    elif N2 > N1:
        lon1 = lon1.repeat(N2)
        lat1 = lat1.repeat(N2)

    return lat1, lon1, lat2, lon2


def gen_id(i=0):
    """
    Produce a generator for sequential integer id values.

    Examples
    --------
    >>> lastorid = 7
    >>> orid = gen_id(lastorid)
    >>> orid.next()
    8
    >>> orid.next()
    9

    Generate more than one at a time:

    >>> orid, arid, wfid = (gen_id() for id in ['orid', 'arid', 'wfid'])
    >>> orid.next(), arid.next()
    (1, 1)

    Dictionary of id generators for desired ids, starting where they left off.
    ids not in Lastid will be missing

    >>> ids = session.query(Lastid).filter(Lastid.keyname.in_(['orid','arid']).all()
    >>> last = dict([(id.keyname, gen_id(id.keyvalue)) for id in ids])
    >>> last['orid'].next()
    8820005

    """
    while 1:
        i += 1
        yield i

ak135 = TauPyModel(model='ak135')

def travel_times(ref, deg=None, km=None, depth=0.):
    """
    Get *approximate* relative travel time(s).

    Parameters
    ----------
    ref : list or tuple of strings and/or floats
        Reference phase names or horizontal velocities [km/sec].
    deg : float, optional
        Degrees of arc between two points of interest (spherical earth).
    km : float, optional
        Horizontal kilometers between two points of interest (spherical earth).
    depth : float, optional. default, 0.
        Depth (positive down) of event, in kilometers.

    Returns
    -------
    numpy.ndarray
        Relative times, in seconds, same length as "ref". NaN if requested time
        is undefined.

    Examples
    --------
    Get relative P arrival and 2.7 km/sec surface wave arrival at 35 degrees
    distance.
    >>> times = travel_times(['P', 2.7], deg=35.0)
    To get absolute window, add the origin time like:
    >>> w1, w2 = times + epoch_origin_time

    Notes
    -----
    Either deg or km must be indicated.
    The user is responsible for adding/subtracting time (such as origin
    time, pre-window noise time, etc.) from those predicted in order to define
    a window.
    Phase travel times use ak135.

    """
    times = np.zeros(len(ref), dtype='float')
    tt = None
    for i, iref in enumerate(ref):
        if isinstance(iref, str):
            # phase time requested
            if not tt:
                if not deg:
                    deg = geod.kilometer2degrees(km)
                tt = ak135.get_travel_times(depth, deg)
            try:
                idx = [ph.name for ph in tt].index(iref)
                itt = [ph.time for ph in tt][idx]
            except ValueError:
                # phase not found
                itt = None
        else:
            # horizontal velocity
            if not km:
                km = deg*(2*math.pi/360.0)*6371.0
            itt = km/iref
        times[i] = itt

    return times


def add_rows(session, rows, recurse=False):
    """Handle common errors with logging in SQLAlchemy add_all.

    Tries to add in bulk.  Failing that, it will rollback and optionally try
    to add one at a time.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    rows : list
        Mapped table instances.
    recurse : bool, optional
        After failure, try to add records individually.

    Returns
    -------
    num : int
        Number of objects added.  0 if none.
    e : exception or None

    """
    e = None
    num = 0
    try:
        session.add_all(rows)
        session.commit()
        num = len(rows)
    except (ProgrammingError, UnmappedInstanceError) as e:
        # IntegrityError: duplicate row(s)
        # ProgrammingError: string encoding problem
        # UnmappedInstanceError: tried to add something like a list or None
        session.rollback()
        logging.warning(str(e))
    except IntegrityError:
        print(str(e))
        session.rollback()
    finally:
        # always executed
        if e and recurse:
            # if an exception was thrown and recursion was requested
            for row in rows:
                i, e = add_rows(session, [row], recurse=False)
                num += i

    return num, e


def get_lastids(session, Lastid, keynames=None, expunge=True, create=False):
    """
    Load or create Lastid instances into a convenient and readable
    attribute-based dictionary.

    Parameters
    ----------
    session : sqlalchemy.orm.Session instance
    Lastid : Lastid table class
    ids : list or tuple of strings
        Lastid.keyname values to load.
    expunge : bool
        If True, expunge loaded ids from the session.  This frees you
        to modify them without affecting the database from which they
        were loaded.  In this case, you'll have to add them back into a
        session and commit them for their changes to be reflected on the
        database.
    create : bool
        If True, create ids that don't already exist.

    Returns
    -------
    last : obspy.core.AttribDict
        Attribute-based dictionary of all lastids.


    Examples
    --------
    Get and set lastid values directly by name or by attribute.
    >>> last = get_lastids(session, Lastid, ['orid', 'arid'])
    >>> last.orid, last['orid']
    Lastid(keyname='orid'), Lastid(keyname='orid')

    Test for their existence by name.
    >>> 'orid' in last
    True

    Use the Lastid's 'next' generator behavior for readable code
    >>> next(last.orid)
    18
    >>> last.orid.keyvalue
    18

    Update your database when you're done.
    >>> session.add_all(ids.values())
    >>> session.commit()

    """

    last = AttribDict()

    q = session.query(Lastid)
    if keynames is None:
        lastids = q.all()
    else:
        lastids = []
        for keyname in keynames:
            lastid = q.filter(Lastid.keyname == keyname).first()
            if lastid:
                lastids.append(lastid)
            elif create:
                lastid = Lastid(keyname=keyname, keyvalue=0)
                session.add(lastid)
                lastids.append(lastid)

    for lastid in lastids:
        if expunge:
            session.expunge(lastid)
        last[lastid.keyname] = lastid

    return last


def get_options(db, prefix=None):
    '''
    for coretable in CORETABLES:
        table_group.add_argument('--' + coretable.name,
                            default=None,
							metavar='owner.tablename',
							dest=coretable.name)
    '''
    options={'url':'sqlite:///'+db, 'prefix':prefix}

    return options


@deprecated('This will be moved to pisces.crud in next version .' + TURNOFFWARNINGSMSG)
def get_or_create_tables(session, create=True, **tables):
    """
    Load or create canonical ORM KB Core table classes.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    create : bool
        If True, create a table object that isn't found.
    tables
        Canonical table name / formatted table name keyword pairs.

    Also accepted are canonical table name keywords with '[owner.]tablename'
    arguments, which will replace any prefix-based core table names.

    Returns
    -------
    tables : dict
        Mapping between canonical table names and SQLA ORM classes.
        e.g. {'origin': MyOrigin, ...}

    """
    # The Plan:
    # 1. For each core table, build or get the table name
    # 2. If it's a vanilla table name, just use a pre-packaged table class
    # 3. If not, try to autoload it.
    # 4. If it doesn't exist, make it from a prototype and create it in the database.

    # TODO: check options for which tables to produce.

    tables = {}
    for coretable in CORETABLES:
        # build the table name
        if options['prefix'] == None:
            fulltablename = coretable.name
        else:
            fulltablename = prefix + coretable.name

        # fulltablename is either an arbitrary string or prefix + core name, but not None

        # put table classes into the tables dictionary
        if fulltablename == coretable.name:
            # it's a vanilla table name. just use a pre-packaged table class instead of making one.
            tables[coretable.name] = coretable.table
        else:
            tables[coretable.name] = make_table(fulltablename, coretable.prototype)

        tables[coretable.name].__table__.create(session.bind, checkfirst=True)

    session.commit()

    return tables


def load_config(config):
    """
    Take dictionary-like object (actual dictionary or ConfigParser section)
    to produce a SQLAlchemy database session and dictionary of database table
    classes.

    Parameters
    ----------
    config : dict-like

    Returns
    -------
    session : SQLAlchemy database session instance
    tables : dict
        Keys are canonical table names, values are SQLAlchemy table classes.

    The config input is a dict-like object of table name keys and class paths.
    This can be a configparser object or a nested dict. The "database" section and "url" key
    are required.  Any additional parameters in the section must be importable
    module names, with optional SQLAlchemy table class names separated by a colon ":".
    If no class name is provided, a class with the capitalized key name is imported.


    Examples
    --------
    The following inputs should be equivalent.

    # pisces.cfg
    [database] # required
    url = oracle://myuser:mypass@dbserver.someplace.gom:1521/dbname # required
    site = mytablemodule:SiteClassName
    wfdisc = mytablemodule:WfdiscClassName
    mytable = custom_tables:MyCustomTableClass
    arrival = othermodule

    >>> config = {'url': 'oracle://myuser:mypass@dbserver.someplace.gom:1521/dbname',
                  'site': 'modulename:SiteClassName',
                  'wfdisc': 'modulename:Wfdisc_raw',
                  'mytable': 'custom_tables:MyCustomTableClass',
                  'arrival': 'othermodule',
                  }
    # or
    >>> import configparser
    >>> config = configparser.ConfigParser()
    >>> config.read('pisces.cfg')
    >>> session, tables = load_config(config['database'])
    >>> tables
    ... {'arrival': othermodule.Arrival,
    ... 'mytable': custom_tables.MyCustomTableClass,
    ... 'site': modulename.SiteClassName,
    ... 'wfdisc': modulename.Wfdisc_raw}

    """
    URL = config.pop('url')
    session = url_connect(URL)

    tables = {}
    for table, classpath in config.items():
        try:
            module_name, class_name = classpath.split(':')
        except ValueError:
            module_name, class_name = classpath, table.capitalize()

        m = import_module(module_name)
        tables[table] = getattr(m, class_name)

    # put it back
    config['url'] = URL

    return session, tables


def make_wildcard_list(toList):
    """
    Take a list, tuple, or comma separated string of variables and output a list
    with sql wildcards '%' and '_'

    Parameters
    ----------
    toList : list, tuple, or comma separated string or variables

    Returns
    -------
    nowList: list of variables contained in the toList variable

    """

    # check if toList is a list and if not, make it a list
    if type(toList) is list:
        nowList = toList

    elif type(toList) is tuple:
        nowList = list(toList)

    elif type(toList) is str:
        nowList = toList.split(',')
    else:
        raise TypeError('input to function make_wildcard_list is not a list, tuple, or comma separated string of variables')

    for x in range(len(nowList)):
       nowList[x] = nowList[x].replace('*','%')
       nowList[x] = nowList[x].replace('?','_')

    return nowList

def glob_to_like(text, escape='\\'):
    """
    Replace FDSN wildcards to equivalent SQL wildcards.

    Replace '*' or '?' glob characters with SQL '%' or '_' LIKE characters,
    escaping any existing literal '%' or '_' characters.

    """
    # TODO: rename fdsn2sql_glob?
    text = text.replace('_', escape + '_').replace('?', '_')
    text = text.replace('%', escape + '%').replace('*', '%')

    return text


def has_sql_wildcards(text, escape='\\'):
    """ Test for non-escaped '_' or '%' SQL wildcard characters in a string.
    """
    # XXX: fails for '_HZ,B\\_Z' ?
    has_wildcards = ('_' in text and escape + '_' not in text) or \
                    ('%' in text and escape + '%' not in text)

    return has_wildcards


def string_expression(selectable, string_filters):
    """
    Produce a SQLAlchemy filter clause on a given string-type column for a
    list of string patterns.

    Produces LIKE statements if wildcards are present, IN when a list is present,
    == when a single non-wildcarded string is present.  Lists may be comma-separated
    strings.

    Takes a SQLAlchemy selectable (e.g. Site.sta) and a list of strings (e.g.
    ['MDJ']) and creates the appropriate SQL filter expression on the provided
    selectable. The string patterns may include LIKE characters '_' and '%'.

    Parameters
    ----------
    selectable : sqlalchemy.orm.attributes.InstrumentedAttribute
        This is simply an ORM Table string-type column, like Site.sta
    string_filters : list of str
        List of one or more strings for subsetting, which may include SQL LIKE
        characters '_' and '%'.  e.g. ['BHZ'], ['%Z', 'BH_'].
        The easiest way to get this for a string list that may be comma separated
        (e.g. '%Z,B_N') is to always use '%Z,B_N'.split(',').

    Returns
    -------
    expression : SQLAlchemy expression
        An expression to be applied with query.filter(expression).  Equivalent
        to a SQL EQUAL, IN, LIKE statement, or an OR statement containing
        EQUAL, IN, or LIKE statements.

    Examples
    --------
    >>> from pisces.tables.css3 import Wfdisc
    >>> channels = ['%Z', 'B_N', 'HHT']
    >>> chan_expr = string_expression(Wfdisc.chan, channels)
    >>> literal_sql(session.bind, chan_expr) # just shows the literal compiled SQL
    "wfdisc.chan LIKE '%Z' OR wfdisc.chan LIKE 'B_N' OR wfdisc.chan = 'HHT'"
    >>> wfdisc_rows = session.query(Wfdisc).filter(chan_expr).all()

"""
    string_filters = string_filters.split(',') if isinstance(string_filters, str) else string_filters

    if len(string_filters) == 1:
        # don't use OR or IN
        string_filter = string_filters[0]
        if has_sql_wildcards(string_filter):
            expression = selectable.like(string_filter)
        else:
            expression = selectable == string_filter
    else:
        # use OR (for wildcards) or IN
        if any([has_sql_wildcards(string_filter) for string_filter in string_filters]):
            # can't use IN, must use LIKE with OR
            # produces query.filter(or_(selectable.like(thing1), selectable == thing2, ...))
            clauses = [selectable.like(string_filter) if has_sql_wildcards(string_filter)
                       else selectable == string_filter
                       for string_filter in string_filters]
            expression = sa.or_(*clauses)
        else:
            # no wildcards, can just use in_
            expression = selectable.in_(string_filters)

    return expression


def literal_sql(engine, statement_or_query):
    # https://stackoverflow.com/questions/5631078/sqlalchemy-print-the-actual-query
    try:
        # it's a query
        statement = statement_or_query.statement
    except AttributeError:
        # it was already a statement
        statement = statement_or_query

    sql = str(statement.compile(engine,
              compile_kwargs={'literal_binds': True}))

    return sql

def _get_entities(query, *requested_classes):
    """
    Get requested table classes from an existing SQLAlchemy query.

    Parameters
    ----------
    query : SQLAlchemy query object
    requested_classes : strings
        Canonical table class names, e.g. 'Site', 'Sitechan', 'Sensor'

    Returns
    -------
    List of SQLAlchemy ORM class, or None where no preferred tables are found

    Examples
    --------
    # if the Sensor class wasn't part of the query.
    >>> get_preferred_entities(query, 'Site', 'Sitechan', 'Sensor')
    [Site , Sitechan, None]

    """
    observed_entities = {
        d["entity"]._tabletype: d["entity"] for d in query.column_descriptions
    }
    return [observed_entities.get(c.capitalize(), None) for c in requested_classes]


def range_filters(*restrictions):
    """Restrict a column to a range.

    Parameters
    ----------
    restrictions : iterable of (ORM column, minvalue, maxvalue) tuples

    Returns
    -------
    list of SQLAlchemy filter conditions that can be unpacked into an SQLAlchemy
    filter method, like query.filter(*filters) for AND clauses,
    or query.filter(or_(*filters)) for OR clauses.

    # e.g.
    >>> f = range_filters((Origin.lat, -10, 15), (Origin.depth, None, 80))
    Produces a list containing zero or one filter expressions.
    It's supplied as a list so it can be applied to a query like:
    >>> query.filter(*f)
    which works even if the list is empty (all ranges are None).

    """
    filters = []
    for column, mn, mx in restrictions:
        if mn is not None:
            if mx is not None:
                filters.append(column.between(mn, mx))
            else:
                filters.append(mn <= column)
        elif mx is not None:
            filters.append(column <= mx)

    return filters


def distance_filter(
    big_query, small_query, degrees=None, kilometers=None, yield_per=None, inverse=False
):
    """
    Return a buffered (yield_per) cartesian product of station (includes Site
    table) query and event query (includes Origin table) results, censored to
    include only those within (or outside of) the provided distance ranges.

    Parameters
    ----------
    big_query : SQLAlchemy query
        Query whos results you expect to be the larger of the two.
        This can be batch-realized with the yield_per keyword.
    small_query : SQLAlchemy query
        Query whos results you expect to be the smaller of the two.
        This will be fully realized in-memory.
    degrees, kilometers : tuple (minradius, maxradius) in degrees, kilometers
        Values may include None (unbounded).
        Both keywords can't be used simultaneously.
    yield_per : int
        Buffer size (joined rows) of the distance calculation.
        If None, all results are realized in memory and returned immediately.
    inverse : bool
        If True, return results that are _outside_ the provided distance ranges.

    Returns
    -------
    list or generator
        If `yield_per` is provided, results are a generator that iterates to yield
        an unknown number list of joined result rows that pass the distance filter
        per iteration, internally processing `yield_per` joined rows at a time.
        If `yield_per` is None, a list of filtered results is returned directly.

    Notes
    -----
    Because this filter must realize query results and do a cartesian join on
    them, it's safest to batch process the results. This argument specifies the
    number of rows processed at a time. SQLAlchemy and Oracle, for example, are
    capable of working with a few thousand results at a time on a reasonable
    machine, depending on how many joined tables are already in the query
    objects provided.  Because the function realizes actual query results, the
    queries provided must be "complete" (i.e. include all the intended SQLAlchemy filters).

    def km_distfn(rows, distrange):
        lat0, lon0 = row[0].lat, row[0].lon
        lat1, lon1 = row[1].lat, row[1].lon
        # calculate kilometers stuff
        return distrange[0] <= dist_value <= distrange[1]

    def deg_distfn(rows, distrange):
        lat0, lon0 = row[0].lat, row[0].lon
        lat1, lon1 = row[1].lat, row[1].lon
        # calculate degrees stuff
        return distrange[0] <= dist_value <= distrange[1]

    # this is an iterator that returns one results row at a time.
    # if yield_per was used, it returns a list of result rows at a time.
    return filter(distfn, query)

    """
    pass

