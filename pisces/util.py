import logging
import math
from getpass import getpass

import numpy as np
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import NoSuchTableError, IntegrityError, OperationalError
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm.exc import NoResultFound, UnmappedInstanceError 

import obspy.core.util.geodetics as geod
from obspy.taup import taup

from pisces.schema.util import PiscesMeta

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

        if backend is 'sqlite':
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


def table_contains_all(itable, keys):
     all([key in itable.columns for key in keys])

#def ormtable(fulltablename, base=None):
#    """
#    For known schema-qualified tables, use:
#    Origin = ormtable('global.origin', base=kb.Origin)
#    For arbitrary tables, use:
#    MyTable = ormtable('jkmacc.sometable')
#    For arbitrary tables without Pisces-specific method, use:
#    MyTable = ormtable('jkmacc.sometable', base=declarative_base())
#    """
#
#    ORMBase = base if base else declarative_base(metaclass=PiscesMeta,
#                                                 constructor=None)
#    parents = (ORMBase,)
#    try:
#        owner, tablename = fulltable.split('.')
#    except ValueError:
#        owner, tablename = None, fulltable
#    if owner:
#        parents += declarative_base(metadata=MetaData(schema=owner)),
#
#    return type(fulltable.capitalize(), parents, {})

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
                    deg = geod.kilometers2degrees(km)
                tt = taup.getTravelTimes(deg, depth, model='ak135')
            try:
                idx = [ph['phase_name'] for ph in tt].index(iref)
                itt = [ph['time'] for ph in tt][idx]
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
        print str(e)
        session.rollback()
    finally:
        # always executed
        if e and recurse:
            # if an exception was thrown and recursion was requested
            for row in rows:
                i, e = add_rows(session, [row], recurse=False)
                num += i

    return num, e
