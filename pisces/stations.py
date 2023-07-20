from sqlalchemy import func, or_
from pisces.util import make_wildcard_list, _get_entities
from obspy.core import UTCDateTime

import warnings

def filter_network(query, net=None, netname=None, auth=None, sta=None,  time_=None, **tables):
    """Filter a network query using Network, Affiliation tables.

    These filters are primarily catagorical. For additional station filtering, queries can be
    passed to and from filter_site() and filter_response() to and from filter_network().

    Parameters
    ----------
    query: sqlalchemy.Query instance
        Includes the required tables for your query (e.g. query = session.query(Network, Affiliation)),
        otherwise they must be provided as keywords (see below).
    net : str [Network, Affiliation]
        Filter Network table on net column.  Wildcards accepted. Multiple nets can be 
        included as a list, tuple, or comma separated string (no spaces).  If Network and Affiliation 
        tables are provided in query or **tables, the Affiliation table is automatically joined to the 
        Network table on the net column.
    netname: str [Network]
        Filter Network table on netname column.  Wildcards accepted. Multiple netnames can be 
        included as a list, tuple, or comma separated string (no spaces).
    auth: str [Network]
        Filter Network table on auth column.  Wildcards accepted. Multiple authors can be 
        included as a list, tuple, or comma separated string (no spaces).
    sta : str [Affiliation]
        Filter Affiliation table on sta column.  Wildcards accepted. Multiple stations can be 
        included as a list, tuple, or comma separated string (no spaces).
    time_ : tuple [Affiliation]
        (starttime, endtime) inclusive range containing int/float/None Unix timestamps. Filters
        Affiliation table on the time and endtime columns.  If starttime or endtime are None, 
        that column is not filtered.
    **tables :
        If a required table isn't in the SELECT of your query, you can provide it
        here as a keyword argument (e.g. site=Site).  It gets used in the filter,
        but isn't included in the final result set (unless it was already in the SELECT).
        If you wish the table included in the result set, use the
        sqlalchemy.orm.Query.add_entity method prior to calling this function.
        e.g. `q = q.add_entity(Site)`

    Joins
    -----
    If Network and Affiliation:
        Network.net == Affiliation.net

    If Site, Sitechan, or Sensor are provided, filter_network() will attempt to join to one of those,
    in that order, on Affilation.sta.

    if Affiliation and Site:
        Site.sta == Affiliation.sta
    elif Affiliation and Sitechan:
        Sitechan.sta == Affiliation.sta
    elif Affiliation and Sensor:
        Sensor.sta == Affiliation.sta
    
    
    Returns
    -------
    query: sqlalchemy.Query instance
        The returned variable is a sqlalchemy query with the filters corresponding to the provided 
        inputs applied.
    
    Examples:
    ---------
    Forgot to include a required table when building query:
    >>> q = session.query(Network)
    >>> try:
    ... q = filter_network(q, sta = 'ANMO')
    ... except ValueError:
    ...     # fails b/c Affiliation isn't in the query
    ...     q = filter_network(q, sta = 'ANMO', affiliation=Affiliation)
    >>> networks = q.all() # list of all networks affiliated with station ANMO

    Get a cartesian join of both networks and stations
    >>> q = session.query(Network, Affiliation)
    >>> q = session.query(Network).add_entity(Affiliation) # equivalent to above
    >>> nets_and_stas = filter_network(q, sta = 'ANMO').all()

    Get a cartesian join of networks to sites
    >>> q = session.query(Network, Affiliation, Site)
    >>> q = session.query(Network, Affiliation).add_entity(Site) # equivalent to above
    >>> nets_and_sites = filter_network(q, sta = 'ANMO').all()

    String handling.  The following queries will produce equivalent results
    >>> q = session.query(Network)
    >>> q = filter_network(q, net = 'SR,IU')
    >>> q = filter_network(q, net = ('SR','IU'))
    >>> q = filter_network(q, net = ['SR',IU'])

    String handling.  Wildcards * and ? are accepted as well as SQL wildcards % and _ .
    >>> q = session.query(Network, Affiliation)
    >>> q = filter_network(q, net = 'SR', sta = ['*'])

    """

    # get desired tables from the query
    Network, Affiliation, Site, Sitechan, Sensor = _get_entities(query, "Network", "Affiliation","Site","Sitechan","Sensor")
    # override if provided
    Network = tables.get("network", None) or Network
    Affiliation = tables.get("affiliation", None) or Affiliation
    Site = tables.get("site", None) or Site
    Sitechan = tables.get("sitechan", None) or Sitechan
    Sensor = tables.get("sensor", None) or Sensor

    # avoid nonsense inputs
    if not any([Network, Affiliation]):
        msg = "Network or Affiliation table required."
        raise ValueError(msg)
    
    if any([netname, auth]) and not Network:
        # Network keywords supplied, but no Network table present
        # TODO: replace with pisces.exc.MissingTableError
        msg = "Network table required."
        raise ValueError(msg)

    if any([sta, time_]) and not Affiliation:
        # Affiliation keywords supplied, but no Affiliation table present
        # TODO: replace with pisces.exc.MissingTableError
        msg = "Affiliation table required."
        raise ValueError(msg)
    
    # join Network and Affiliation if both present
    if Network and Affiliation:
        query = query.filter(Network.net == Affiliation.net)

    # if query contains Site, Sitechan, or Sensor, append to Affiliation 
    # in order of Site, else Sitechan, else Sensor
    if Affiliation and Site:
        query = query.filter(Site.sta == Affiliation.sta)
    elif Affiliation and Sitechan:
        query = query.filter(Sitechan.sta == Affiliation.sta)
    elif Affiliation and Sensor:
        query = query.filter(Sensor.sta == Affiliation.sta)

    if net:
        net = make_wildcard_list(net)
        query = query.filter(or_(*[Network.net.like(nets) for nets in net]))
    
    if netname:
        netname = make_wildcard_list(netname)
        query = query.filter(or_(*[Network.netname.like(netnames) for netnames in netname]))
    
    if auth:
        auth = make_wildcard_list(auth)
        query = query.filter(or_(*[Network.net.like(auths) for auths in auth]))

    if sta:
        sta = make_wildcard_list(sta)
        query = query.filter(or_(*[Affiliation.sta.like(stas) for stas in sta]))

    if time_:
        t1, t2 = time_
        t1 = UTCDateTime(t1).timestamp if t1 else None
        t2 = UTCDateTime(t2).timestamp if t2 else None
        if t1:
            query = query.filter(t1 <= Affiliation.endtime)
        if t2:
            query = query.filter(t2 >= Affiliation.time)

    return query


def filter_site(query, sta=None, chan=None, time_=None, staname = None, refsta = None, **tables):
    """Filter a site query using Site, Sitechan tables.

    These filters are primarily geograpchical and catagorical. For additional station filtering, queries can be
    passed to and from filter_network() and filter_response() to and from filter_site().

    Parameters
    ----------
    query: sqlalchemy.Query instance
        Includes the required tables for your query (e.g. query = session.query(Site, Sitechan)),
        otherwise they must be provided as keywords (see below).
    sta : str [Site, Sitechan]
        Filter Site or Sitechan table on sta column.  Wildcards accepted. Multiple stations can be 
        included as a list, tuple, or comma separated string (no spaces). If Site and Sitechan tables
        is provided in query or **tables, the Site table is automatically joined to the 
        Sitechan table on the sta column.
    chan : str [Sitechan]
        Filter Sitechan table on chan column.  Wildcards accepted. Multiple chans can be 
        included as a list, tuple, or comma separated string (no spaces). 
    time_ : tuple [Site, Sitechan]
        (starttime, endtime) inclusive range containing int following the format YYYYDDD for the 
        4 character year and the 3 character julian day. Filters Site or Sitechan table on the time 
        and endtime columns.  If starttime or endtime are None, that column is not filtered. If both 
        Site and Sitechan are provided, Site will be further filtered by 
        Sitechan.ondate.between(Site.ondate, Site.offdate)
    staname: str [Site]
        Filter Site table on staname column.  Wildcards accepted. Multiple stanames can be 
        included as a list, tuple, or comma separated string (no spaces).
    refsta: str [Site]
        Filter Site table on refsta column.  Wildcards accepted. Multiple refstas can be 
        included as a list, tuple, or comma separated string (no spaces).
    **tables :
        If a required table isn't in the SELECT of your query, you can provide it
        here as a keyword argument (e.g. affiliation=Affiliation).  It gets used in the filter,
        but isn't included in the final result set (unless it was already in the SELECT).
        If you wish the table included in the result set, use the
        sqlalchemy.orm.Query.add_entity method prior to calling this function.
        e.g. `q = q.add_entity(Affiliation)`

    Joins
    -----
    If Site and Sitechan:
        Site.sta == Sitechan.sta

    If time_ and Sitechan:
        Sitechan.ondate.between(Site.ondate, Site.offdate)

    If Affiliation or Sensor are provided, filter_site() will attempt to join to each of those in the 
    following order:
        if Sitechan and Sensor
            Sitechan.chanid == Sensor.chanid
        else if  Site and Sensor
            Site.sta == Sensor.sta    
               
        if Site and Affiliation
            Site.sta == Affiliation.sta
        else if Sitechan and Affiliation
            Sitechan.sta == Affiliation.sta
        
    Returns
    -------
    query: sqlalchemy.Query instance
        The returned variable is a sqlalchemy query with the filters corresponding to the provided 
        inputs applied.
    
    Examples:
    ---------
    See filter_network() docstring for usage examples.

    """
   
     # get desired tables from the query
    Site, Sitechan, Sensor, Affiliation = _get_entities(query, "Site","Sitechan","Sensor","Affiliation")
    # override if provided
    Affiliation = tables.get("affiliation", None) or Affiliation
    Site = tables.get("site", None) or Site
    Sitechan = tables.get("sitechan", None) or Sitechan
    Sensor = tables.get("sensor", None) or Sensor

    if not any([Site, Sitechan]):
        msg = "Site or Sitechan table required."
        raise ValueError(msg)

    if any([staname, refsta]) and not Site:
        # Site keywords supplied, but no Site table present
        # TODO: replace with pisces.exc.MissingTableError
        msg = "Site table required."
        raise ValueError(msg)

    if chan and not Sitechan:
        # Sitechan keywords supplied, but no Sitechan table present
        # TODO: replace with pisces.exc.MissingTableError
        msg = "Sitechan table required."
        raise ValueError(msg)
    
    # Join Ste and Sitechan if both present
    if Site and Sitechan:
        query = query.filter(Site.sta == Sitechan.sta)
    
    # If Sensor is present join first on Sitechan.chanid if Sitechan present
    # Else join on Site.sta
    if Sensor:
        if Sitechan:
            query = query.filter(Sitechan.chanid == Sensor.chanid)
        else:
            query = query.filter(Sensor.sta == Site.sta)

    # If Affiliation is present join first on Site.sta if Site present
    # Else join on Sitechan.sta 
    if Affiliation:
        if Site:
            query = query.filter(Site.sta == Affiliation.sta)
        else:
            query =query.filter(Sitechan.sta == Affiliation.sta)

    if sta:
        sta = make_wildcard_list(sta)
        if Site:
            query = query.filter(or_(*[Site.sta.like(stas) for stas in sta]))
        else:
            query = query.filter(or_(*[Sitechan.sta.like(stas) for stas in sta]))
    
    if chan:
        chan = make_wildcard_list(chan)
        query = query.filter(or_(*[Sitechan.chan.like(chans) for chans in chan]))


    # Filter by ondate and offdate which are year and julian day represented as integers
    if time_:
        t1, t2 = time_
        t1 = int(UTCDateTime(t1).strftime('%Y%j')) if t1 else None
        t2 = int(UTCDateTime(t2).strftime('%Y%j')) if t2 else None
        
        # If Sitechan is present filter there and the join Sitechan to Site based 
        # on ondate, otherwise channels will be joined on Site ranges where channels 
        # may not actually exist.  If not Sitechan, filter on Site
        if Sitechan:
            if t1:
                query = query.filter(t1 <= Sitechan.offdate)
            if t2: 
                query = query.filter(t1 >= Sitechan.ondate)
            if Sitechan and Site:
                query =query.filter(Sitechan.ondate.between(Site.ondate, Site.offdate))
        else:
            if t1:
                query = query.filter(t1 <= Site.offdate)
            if t2: 
                query = query.filter(t1 >= Site.ondate)
    
    if staname:
        staname = make_wildcard_list(staname)
        query = query.filter(or_(*[Site.staname.like(stanames) for stanames in staname]))
    
    if refsta:
        refsta = make_wildcard_list(refsta)
        query = query.filter(or_(*[Site.refsta.like(refstas) for refstas in refsta]))

    return query

def filter_response(query, sta = None, chan = None, time_ = None, **tables):
    """Filter query for instrument response information using the Sensor and Instrument tables.

    These filters are primarily catagorical. For additional station filtering, queries can be
    passed to and from filter_network() and filter_site() to and from filter_response().

    filter_response() only provides the response information in database tables.  Actual 
    response files will need to be read in separately from the dir and dfile columns returned
    in the Instrument table.

    Parameters
    ----------
    query: sqlalchemy.Query instance
        Includes the required tables for your query (e.g. query = session.query(Sensor, Instrument)),
        otherwise they must be provided as keywords (see below).  Both Sensor and Instrument are required
        and are joined on the inid column,
    sta : str [Sensor]
        Filter Sensor on sta column.  Wildcards accepted. Multiple stations can be 
        included as a list, tuple, or comma separated string (no spaces).
    chan : str [Sensor]
        Filter Sensor table on chan column.  Wildcards accepted. Multiple chans can be 
        included as a list, tuple, or comma separated string (no spaces). 
    time_ : tuple [Sensor]
        (starttime, endtime) inclusive range containing int/float/None Unix timestamps. Filters
        Sensor table on the time and endtime columns.  If starttime or endtime are None, 
        that column is not filtered.
    **tables :
        If a required table isn't in the SELECT of your query, you can provide it
        here as a keyword argument (e.g. sitechan=Sitechan).  It gets used in the filter,
        but isn't included in the final result set (unless it was already in the SELECT).
        If you wish the table included in the result set, use the
        sqlalchemy.orm.Query.add_entity method prior to calling this function.
        e.g. `q = q.add_entity(Sitechan)`

    Joins
    -----
    Sensor.inid == Instrument.inid

    If Sitechan, Site, or Affiliation are provided, filter_response() will attempt to join to each of those in the 
    following order:
        if Sitechan
            Sitechan.chanid == Sensor.chanid
        else if  Site
            Site.sta == Sensor.sta
        else if Affiliation
            Affiliation.sta == Sensor.sta
        
    Returns
    -------
    query: sqlalchemy.Query instance
        The returned variable is a sqlalchemy query with the filters corresponding to the provided 
        inputs applied.
    
    Examples:
    ---------
    See filter_network() docstring for usage examples.

    """
    # get desired tables from the query
    Affiliation, Site, Sitechan, Sensor, Instrument = _get_entities(query,"Affiliation","Site","Sitechan","Sensor", "Instrument")
    # override if provided
    Affiliation = tables.get("affiliation", None) or Affiliation
    Site = tables.get("site", None) or Site
    Sitechan = tables.get("sitechan", None) or Sitechan
    Sensor = tables.get("sensor", None) or Sensor
    Instrument = tables.get("instrument", None) or Instrument

    # avoid nonsense inputs
    if not Sensor and Instrument:
        msg = "Sensor and Instrument table required."
        raise ValueError(msg)

    # Join Sensor and Instrument since both are always required for responses 
    query = query.filter(Sensor.inid == Instrument.inid)

    # If Sitechan, Site, or Affiliation are present join first on Sitechan.chanid
    # Then try to join on Site.sta, then try to join on Affiliation.sta
    if Sitechan:
        query = query.filter(Sitechan.chanid == Sensor.chanid)
    elif Site:
        query = query.filter(Sensor.sta == Site.sta)
    elif Affiliation:
        query = query.filter(Sensor.sta == Affiliation.sta)

    if sta:
        sta = make_wildcard_list(sta)
        query = query.filter(or_(*[Sensor.sta.like(stas) for stas in sta]))

    if chan:
        chan = make_wildcard_list(chan)
        query = query.filter(or_(*[Sensor.chan.like(chans) for chans in chan]))

    if time_:
        t1, t2 = time_
        t1 = UTCDateTime(t1).timestamp if t1 else None
        t2 = UTCDateTime(t2).timestamp if t2 else None
        if t1:
            query = query.filter(t1 <= Sensor.endtime)
        if t2:
            query = query.filter(t2 >= Sensor.time)

    return query

def assign_unique_net(q, network_name, affiliation_name, pref_nets = None, two_char_code = True, first_available = True, default_net = '__'):
    return 

def check_orphan_stas():
    return
