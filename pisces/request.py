"""
Convenience functions for building common queries.

"""
import numpy as np
from sqlalchemy import func, or_
from obspy.core import UTCDateTime, Stream
import obspy.geodetics as geod

from pisces.io.trace import wfdisc2trace
from pisces.util import make_wildcard_list

import warnings

def get_wfdisc_rows(session, wfdisc, sta=None, chan=None, t1=None, t2=None,
                    wfids=None, daylong=False, asquery=False, verbose=False):
    """
    Returns a list of wfdisc records from provided SQLAlchemy ORM mapped
    wfdisc table, for given station, channel, and time window combination.

    Parameters
    ----------
    session: bound session instance
    wfdisc: SQLAlchemy mapped wfdisc table
    sta, chan, : str, optional
        station, channel strings,
    t1, t2 : int, optional
        Epoch time window of interest (seconds)
        Actually searches for wfdisc.time between t1-86400 and t2 and
        wfdisc.endtime > t1
    wfids : list of integers, optional
        wfid integers. Obviates other arguments.
    daylong : bool, optional
        If True, uses a slightly different time query for best results.
        Not yet implemented (is currently the default behavior).
    asquery : bool, optional
        Return the query object instead of the results.  Default, False.
        Useful if additional you desire additional sorting of filtering.
    verbose : bool, optional
        Print request to the stdout. Not used with asquery=True.

    Returns
    -------
    list of wfdisc row objects, or sqlalchemy.orm.Query instance

    """
    # seconds in a wfdisc file
    CHUNKSIZE = 24 * 60 * 60
    q = session.query(wfdisc)
    if wfids is not None:
        q = q.filter(wfdisc.wfid.in_(wfids))
    else:
        if sta is not None:
            sta = make_wildcard_list(sta)
            q = q.filter(or_(*[wfdisc.sta.like(stas) for stas in sta]))
        if chan is not None:
            chan = make_wildcard_list(chan)
            q = q.filter(or_(*[wfdisc.chan.like(chans) for chans in chan]))
        if [t1, t2].count(None) == 0:
            q = q.filter(wfdisc.time.between(t1 - CHUNKSIZE, t2))
            q = q.filter(wfdisc.endtime > t1)
        else:
            if t1 is not None:
                q = q.filter(wfdisc.time >= t1 - CHUNKSIZE)
                q = q.filter(wfdisc.endtime > t1)
            if t2 is not None:
                q = q.filter(wfdisc.time <= t2)

    if asquery:
        res = q
    else:
        if verbose:
            msg = "Requesting sta={}, chan={}, time=[{}, {}], wfids={}"
            print(msg.format(sta, chan, UTCDateTime(t1), UTCDateTime(t2), wfids))
        res = q.all()

    return res


def distaz_query(records, deg=None, km=None, swath=None):
    """
    Out-of-database subset based on distances and/or azimuths.

    Parameters
    ----------
    records : iterable of objects with lat, lon attribute floats
        Target of the subset.
    deg : list or tuple of numbers, optional
        (centerlat, centerlon, minr, maxr)
        minr, maxr in degrees or None for unconstrained.
    km : list or tuple of numbers, optional
        (centerlat, centerlon, minr, maxr)
        minr, maxr in km or None for unconstrained.
    swath : list or tuple of numbers, optional
        (lat, lon, azimuth, tolerance)
        Azimuth (from North) +/-tolerance from lat,lon point in degrees.

    Returns
    -------
    list
        Subset of supplied records.

    """
    #initial True array to propagate through multiple logical AND comparisons
    mask0 = np.ones(len(records), dtype=bool)

    if deg:
        dgen = (geod.locations2degrees(irec.lat, irec.lon, deg[0], deg[1]) \
                for irec in records)
        degrees = np.fromiter(dgen, dtype=float)
        if deg[2] is not None:
            mask0 = np.logical_and(mask0, deg[2] <= degrees)
        if deg[3] is not None:
            mask0 = np.logical_and(mask0, deg[3] >= degrees)

        #mask0 = np.logical_and(mask0, mask)

    if km:
        #???: this may be backwards
        mgen = (geod.gps2dist_azimuth(irec.lat, irec.lon, km[0], km[1])[0] \
                  for irec in records)
        kilometers = np.fromiter(mgen, dtype=float)/1e3
        #meters, azs, bazs = zip(*valgen)
        #kilometers = np.array(meters)/1e3
        if km[2] is not None:
            mask0 = np.logical_and(mask0, km[2] <= kilometers)
        if km[3] is not None:
            mask0 = np.logical_and(mask0, km[3] >= kilometers)

        #mask0 = np.logical_and(mask0, mask)

    if swath is not None:
        minaz = swath[2] - swath[3]
        maxaz = swath[2] + swath[3]
        #???: this may be backwards
        azgen = (geod.gps2dist_azimuth(irec.lat, irec.lon, km[0], km[1])[1] \
                 for irec in records)
        azimuths = np.fromiter(azgen, dtype=float)
        mask0 = np.logical_and(mask0, azimuths >= minaz)
        mask0 = np.logical_and(mask0, azimuths <= maxaz)

    #idx = np.nonzero(np.atleast_1d(mask0))[0] ???
    idx = np.nonzero(mask0)[0]
    recs = [records[i] for i in idx]

    return recs


def geographic_query(q, table, region=None, depth=None, asquery=False):
    """
    Filter by region (W, E, S, N) [deg] and/or depth range (min, max) [km].

    """
    if region:
        #(W,E,S,N)
        if region.count(None) == 0:
            q = q.filter(table.lon.between(region[0], region[1]))
            q = q.filter(table.lat.between(region[2], region[3]))
        else:
            if region[0] is not None:
                q = q.filter(table.lon > region[0])
            if region[1] is not None:
                q = q.filter(table.lon < region[1])
            if region[2] is not None:
                q = q.filter(table.lat > region[2])
            if region[3] is not None:
                q = q.filter(table.lat < region[3])

    if depth:
        #(mindep,maxdep)
        if depth.count(None) == 0:
            q = q.filter(table.depth.between(depth[0], depth[1]))
        else:
            if depth[0]:
                q = q.filter(table.depth >= depth[0])
            if depth[1]:
                q = q.filter(table.depth <= depth[1])

    if asquery:
        res = q
    else:
        res = q.all()

    return res

def netstachan_query(q, stations=None, channels=None, networks=None, 
        asquery=False):
    pass

def time_query(q, time=None, daylong=False, asquery=False):
    pass

def get_events(session, origin, event=None, region=None, deg=None, km=None, 
        swath=None, mag=None, depth=None, etime=None, orids=None, evids=None, 
        prefor=False, asquery=False):
    """
    Build common queries for events.

    Parameters
    ----------
    session : sqlalchemy.orm.Session instance
        Must be bound.
    origin : mapped Origin table class
    event : mapped Event table class, optional
    region : list or tuple of numbers, optional
        (W, E, S, N) in degrees. Default, None.
    deg : list or tuple of numbers, optional
        (centerlat, centerlon, minr, maxr) . Default, None.
        minr, maxr in degrees or None for unconstrained.
    km : list or tuple of numbers, optional
        (centerlat, centerlon, minr, maxr)  Default, None.
        minr, maxr in km or None for unconstrained.
    swath : list or tuple of numbers, optional
        (lat, lon, azimuth, tolerance)
        Azimuth (from North) +/-tolerance from lat,lon point in degrees.
        Not yet implemented.
    mag : dict, optional
        {'type1': [min1, max1], 'type2': [min2, max2], ...}
        'type' can be 'mb', 'ms', or 'ml'.  Produces OR clauses.
    depth : tuple or list, optional
        Depth interval [mindep, maxdep] in km.
        Use None for an unconstrained limit.
    etime : tuple or list, optional
        (tstart, tend) epoch event time window
        Use None for an unconstrained limit.
    orids, evids : list or tuple of int, optional
        orid, evid numbers < 1000 in length
        Evids requires event table.
    prefor : bool, optional
        Return preferred origins only. Default False.  Requires event table
        be provided.
    asquery : bool, optional
        Return the query object instead of the results.  Default, False.
        Useful if additional you desire additional sorting of filtering, or
        if you have your own in-database geographic query function(s).  If 
        supplied, deg, km, and/or swath are ignored in the returned query.

    Returns
    -------
    sqlalchemy.orm.Query instance

    Notes
    -----
    Each keyword argument corresponds to an AND clause, except 'mag' which
    returns OR clauses.  Don't submit a request containing both 'evids' and
    'orids' unless you want them joined by an AND clause.  Otherwise process
    them individually, then collate and unique them afterwards.

    """
    Origin = origin
    Event = event

    t = etime

    q = session.query(Origin)

    if orids:
        #[orid1,orid2,...]
        q = q.filter(Origin.orid.in_(orids))

    if t:
        if t.count(None) == 0:
            q = q.filter(Origin.time.between(t[0], t[1]))
        else:
            if t[0]:
                q = q.filter(Origin.time > t[0])
            if t[1]:
                q = q.filter(Origin.time < t[1])

    if mag:
        #TODO: use list comprehension
        magclause = []
        for magtype, vals in mag.iteritems():
            magclause.append(getattr(Origin, magtype).between(vals[0], vals[1]))
        q = q.filter(or_(*magclause))

    if evids:
        q = q.filter(Origin.evid == Event.evid)
        q = q.filter(Event.evid.in_(evids))

    if prefor:
        #q = q.join(Event,Origin.evid==Event.evid)
        #q = q.add_columns(Origin.evid)
        q = q.filter(Origin.orid==Event.prefor)

    q = geographic_query(q, Origin, region=region, depth=depth, asquery=True)

    if asquery:
        res = q
    else:
        res = distaz_query(q.all(), deg=deg, km=km, swath=swath)

    return res
 

def get_stations(session, site, sitechan=None, affiliation=None, stations=None, 
        channels=None, nets=None, loc=None, region=None, deg=None, km=None, 
        swath=None, time_span=None, asquery=False):
    """
    Build common queries for stations.

    Parameters
    ----------
    session : sqlalchemy.orm.Session instance
        Must be bound.
    site : mapped Site table class
    sitechan : mapped Sitechan table class, optional
    affiliation : mapped Affiliation table class, optional
    stations : list or tuple of strings
        Desired station code strings.
    channels, nets : list or tuple of strings, or single regex string, optional
        Desired channel, network code strings or regex
    loc : list/tuple, optional
        Location code.
        Not yet implemented.
    region : tuple or list of numbers, optional
        Geographic (W,E,S,N) in degrees, None values for unconstrained.
    deg : list or tuple of numbers, optional
        (centerlat, centerlon, minr, maxr)
        minr, maxr in degrees or None for unconstrained.
    km : list or tuple of numbers, optional
        (centerlat, centerlon, minr, maxr)
        minr, maxr in km or None for unconstrained.
    swath : list or tuple of numbers, optional
        (lat, lon, azimuth, tolerance)
        Azimuth (from North) +/-tolerance from lat,lon point in degrees.
        Currently only works in gnem Oracle.
    asquery : bool, optional
        Return the query object instead of the results.  Default, False.
        Useful if additional you desire additional sorting of filtering, or
        if you have your own in-database geographic query function(s).  If 
        supplied, deg, km, and/or swath are ignored in the returned query.
    time_span : tuple or list
        (startdate, enddate) or [startdate, enddate]
        startdate and enddate are integer julian days of when you want stations (YYYYddd).  
        If stations were moved one or more times in the time_span, you will 
        get multiple copies of the station with updated gps values. If you want to be 
        guaranteed a specific station at a specific time, startdate and enddate must 
        both be included, even if they are the same.

    Notes
    -----
    Each parameter produces an AND clause, list parameters produce IN 
    clauses, a regex produces a REGEXP_LIKE clause (Oracle-specific?).

    deg, km, and swath are evaluated out-of-database by evaluating all other 
    flags first, then masking.  This can be memory-intensive.  See "Examples"
    for how to perform in-database distance filters.
    
    To include channels or networks with your results use asquery=True, and

    >>> q = q.add_columns(Sitechan.chan)
    >>> q = q.add_columns(Affiliation.net)

    with the returned query.

    Examples
    --------
    Use your own in-database distance query function "km_from_point":

    >>> from sqlalchemy import func
    >>> q = get_stations(session, site, channels=['BHZ'], region=(65,75,30,40), asquery=True)
    >>> stations = q.filter(func.km_from_point(site.lat, site.lon, 40, -110) < 100).all()

    """
    #XXX: remove dependency on func.regexp_like
    Site = site
    Sitechan = sitechan
    Affiliation = affiliation

    d = deg
    
    q = session.query(Site)
    
    if stations:
        stations = make_wildcard_list(stations)
        q = q.filter(or_(*[Site.sta.like(stas) for stas in stations]))
        
    if nets:
        nets = make_wildcard_list(nets)
        q = q.join(Affiliation, Affiliation.sta==Site.sta)
        q = q.filter(or_(*[Affiliation.net.like(net) for net in nets]))

    if channels:
        channels = make_wildcard_list(channels)
        q = q.join(Sitechan, Sitechan.sta==Site.sta)
        q = q.filter(or_(*[Sitechan.chan.like(chans) for chans in channels]))

    if time_span:
        start_date, end_date = time_span  # start and end days of time period to get stations from
        if start_date is not None:
            q = q.filter(Site.ondate <= start_date)
        if end_date is not None:
            q = q.filter(Site.offdate >= end_date)

    q = geographic_query(q, Site, region=region, asquery=True)

    if asquery:
        res = q
    else:
        res = distaz_query(q.all(), deg=deg, km=km, swath=swath)

    return res


def get_arrivals(session, arrival, assoc=None, stations=None, channels=None, 
        atime=None, phases=None, arids=None, orids=None, auth=None, 
        asquery=False):
    """
    Build common queries for arrivals.
    
    Parameters
    ----------
    stations, channels : list or tuple of strings
        Desired station, channel strings.
    arrival: mapped Arrival table class
    assoc: mapped Assoc table class, optional
    atime : tuple or list of float, optional
        (tstart, tend) epoch arrival time window. Either can be None.
    phases: list or tuple of strings
        Arrival 'iphase'.
    arids : list of integers
        Desired arid numbers.
    orids : list of integers
        orids from which associated arrivals will be returned. Requires Assoc
        table.
    auth : list/tuple of strings
        Arrival author list.

    Returns
    -------
    list or sqlalchemy.orm.Query instance
        Arrival results.

    Notes
    -----
    Each argument adds an AND clause to the SQL query.
    Unspecified (keyword) arguments are treated as wildcards.  That is, no
    arguments means, "give me all arrivals everywhere ever."

    """
    Arrival = arrival
    Assoc = assoc

    t = atime

    q = session.query(Arrival)

    if stations:
        stations = make_wildcard_list(stations)
        q = q.filter(or_(*[Arrival.sta.like(stas) for stas in stations]))

    if channels:
        channels = make_wildcard_list(channels)
        q = q.filter(or_(*[Arrival.chan.like(chans) for chans in channels]))

    if phases:
        phases = make_wildcard_list(phases)
        q = q.filter(or_(*[Arrival.iphase.like(phase) for phase in phases]))

    if t:
        if t.count(None) == 0:
            q = q.filter(Arrival.time.between(t[0], t[1]))
        else:
            if t[0]:
                q = q.filter(Arrival.time > t[0])
            if t[1]:
                q = q.filter(Arrival.time < t[1])

    if arids:
        q = q.filter(Arrival.arid.in_(arids))

    if orids:
        q = q.filter(Arrival.arid == Assoc.arid)
        q = q.filter(Assoc.orid.in_(orids))

    if auth:
        auth = make_wildcard_list(auth)
        q = q.filter(or_(*[Arrival.auth.like(author) for author in auth]))

    if asquery:
        res = q
    else:
        res = q.all()

    return res


def get_waveforms(session, wfdisc, station=None, channel=None, starttime=None,
                  endtime=None, wfids=None, tol=None, asquery=False):
    """
    Request waveforms.

    Parameters
    ----------
    session : sqlalchemy.orm.Session instance
        Must be bound.
    wfdisc : mapped Wfdisc table class
    station, channel : str, optional
        Desired station, channel code strings
    starttimes, endtimes : float, optional
        Epoch start times, end times.
        Traces will be cut to these times.
    wfids : iterable of int, optional
        Wfdisc wfids.  Obviates the above arguments and just returns full Wfdisc
        row waveforms.
    tol : float
        If provided, a warning is fired if any Trace is not within tol seconds
        of starttime and endtime.
    asquery : bool, optional
        Return the query object instead of the results.  Default, False.
        Useful if additional you desire additional sorting of filtering.

    Returns
    -------
    obspy.Stream
        Traces are merged and cut to requested times.

    """
    # TODO: add evids= option?, use with stawin= option in .execute method?
    # TODO: implement get_arrivals if arrivals=True
    Wfdisc = wfdisc

    # st = Stream()
    if wfids:
        station = channel = starttime = endtime = None

    starttime = float(starttime) if starttime is not None else None
    endtime = float(endtime) if endtime is not None else None

    t1_utc = UTCDateTime(starttime) if starttime is not None else None
    t2_utc = UTCDateTime(endtime) if endtime is not None else None

    wfs = get_wfdisc_rows(session, Wfdisc, station, channel, starttime, endtime,
                          wfids=wfids, asquery=asquery)

    if asquery:
        res = wfs
    else:
        res = wfdisc_rows_to_stream(wfs, t1_utc, t2_utc, tol=tol)

    return res
    

def wfdisc_rows_to_stream(wf_rows, start_t, end_t, tol=None):
    """
    Convert wfdisc rows to obspy stream, trim the data to starttime and endtime 
    in the process

    Parameters
    ----------
    wf_rows : 
        Wfdisc rows as generated by get_wfdisc_rows or similar
    start_t: UTCDateTime
        Requested start time of the returned traces
    end_t: UTCDateTime
        Requested end time of the returned traces
    tol: float
        If provided, a warning is fired if any Trace is not within tol seconds 
        of starttime and endtime

    Returns
    -------
    obspy.Stream
        Traces are merged and trimmed to requested times

    Raises
    ------
    ValueError:
        Returned Stream contains trace start/end times outside of the tolerance.
    """
    st = Stream()
    
    for wf in wf_rows:
        try:
            tr = wfdisc2trace(wf)
        except IOError:
            # can't read file
            # XXX: wow, why the hell would I let unreadable traces slip past
            tr = None

        if tr:
            # None utc times will pass through
            tr.trim(start_t, end_t)
            st.append(tr)
            # TODO: do arrival stuff here?

    if all([tol, start_t, end_t]):
        start_t, end_t = zip(*[(tr.stats.start_t, tr.stats.end_t) for tr in st])
        min_t = float(min(start_t))
        max_t = float(max(end_t))
        if (abs(min_t - start_t) > tol) or (abs(max_t - end_t) > tol):
            msg = "Trace times are outside of tolerance: {} seconds".format(tol)
            # XXX: change this to a real Pisces exception
            raise ValueError(msg)

    return st


def get_ids(session, lastid, ids, detach=False):
    """
    Get or create lastid rows.

    Parameters
    ----------
    session : sqlalchemy.orm.session instance, bound
    lastid : sqlalchemy orm mapped lastid table
    ids : list
        Desired lastid keyname strings.
    detach : bool, optional
        If True, expunge results from session before returning.
        Useful if you don't have permission on lastid, and don't want
        session commits to throw a permission error.


    Returns
    -------
    list
        Corresponding existing or new rows from lastid table.

    Notes
    -----
    Keyvalue is 0 if id name not present in lastid table.

    """
    out = []
    for idname in ids:
        iid = session.query(lastid).filter(lastid.keyname == idname).first()
        if not iid:
            iid = lastid(keyname=idname, keyvalue=0)
        out.append(iid.keyvalue)

    if detach:
        session.expunge_all(out)

    return out

def query_network(session, network, nets=None, affiliation=None, stas=None, time_=None, endtime=None, with_query = None):
    """
    Parameters
    ----------
    session : sqlalchemy.orm.session instance, bound
    network : 
    nets : 
    affiliation : 
    stas :
    time_ :
    endtime : 
    pref_nets : 
    with_query :
    site_name :  
    Returns
    -------
    query
        sdfs
    
    Notes:
    ------
    If input into get_networks is a query, an affiliation table must be provided and the query must contain a site table to be
    joined on affiliation.sta == site.sta .

    Results cannot be filtered with a station list if affiliation table is not provided.
    """
    if with_query:
        if not affiliation:
            raise NameError('Affiliation table must be provided when get_networks is given a query as input')   

        q = with_query

        site = None
        sitechan = None
        sensor = None

        for i in q.column_descriptions:
            checkEntity = i['entity']
            if checkEntity._tabletype == 'Site':
                site = checkEntity
            if checkEntity._tabletype == 'Sitechan':
                sitechan = checkEntity
            if checkEntity._tabletype == 'Sensor':
                sensor = checkEntity
        
        if site:
            q = q.add_entity(affiliation)
            q = q.join(affiliation, affiliation.sta == site.sta)
            q = q.add_entity(network)
            q = q.join(network, network.net == affiliation.net)

        elif sitechan:
            q = q.add_entity(affiliation)
            q = q.join(affiliation, affiliation.sta == sitechan.sta)
            q = q.add_entity(network)
            q = q.join(network, network.net == affiliation.net)
            warnings.warn("No site table is given in provided query.  Joining Affiliation on Sitechan")
        
        elif sensor:
            q = q.add_entity(affiliation)
            q = q.join(affiliation, affiliation.sta == sensor.sta)
            q = q.add_entity(network)
            q = q.join(network, network.net == affiliation.net)
            warnings.warn("No Site or Sitechan table is given in provided query.  Joining Affiliation on Sensor")

        else:
            raise NameError('No table with a sta column on which to join Affiliation is in the provided query')

    else:
        q = session.query(network)
        if affiliation:
            q = q.add_entity(affiliation)
            q = q.join(affiliation, affiliation.net==network.net)

    if nets:
        nets = make_wildcard_list(nets)
        q = q.filter(or_(*[network.net.like(net) for net in nets]))

    if stas:
        if not affiliation:
            raise NameError('Affiliation table required to filter Network table from station list')
        stas = make_wildcard_list(stas)
        q = q.filter(or_(*[affiliation.sta.like(sta) for sta in stas]))

    if time_:
        if not affiliation:
            raise NameError('Affiliation table required to use starttime filtering')
        q = q.filter(time_.timestamp < affiliation.endtime)

    if endtime:
        if not affiliation:
            raise NameError('Affiliation table required to use endtime filtering')
        q = q.filter(endtime.timestamp > affiliation.time)

    return q


def query_site(session, site, sitechan=None, stas=None, chans=None, time_=None, endtime=None, with_query = None):
    """
    Parameters
    ----------
    session : sqlalchemy.orm.session instance, bound
    site : 
    sitechan : 
    stas : 
    chans :
    time_ :
    endtime :  
    with_query :
    affiliation_name :
    sensor_name:

    Returns
    -------
    query
        sdfs
    
    Notes:
    ------
    
    """
    if with_query:

        q = with_query
        
        affiliation = None
        sensor = None

        for i in q.column_descriptions:
            checkEntity = i['entity']
            if checkEntity._tabletype == 'Affiliation':
                affiliation = checkEntity
            if checkEntity._tabletype == 'Sensor':
                sensor = checkEntity
        
        if affiliation and sensor:
            q = q.add_entity(site)
            q = q.join(site, affiliation.sta == site.sta)
            if sitechan:
                q = q.add_entity(sitechan)
                q = q.join(sitechan, site.sta == sitechan.sta)
                q = q.join(sitechan, sitechan.chanid == sensor.chanid)
            else:
                q = q.join(sensor, site.sta == sensor.sta)
                warnings.warn("No sitechan specified, joining site to sensor on column sta")

        elif  affiliation:
            q = q.add_entity(site)
            q = q.join(site, affiliation.sta == site.sta)
            if sitechan:
                q = q.add_entity(sitechan)
                q = q.join(sitechan, site.sta == sitechan.sta)

        elif sensor:
            if sitechan:
                q = q.add_entity(sitechan)
                q = q.join(sitechan, sitechan.chanid == sensor.chanid)
                q = q.add_entity(site)
                q = q.join(site, site.sta == sensor.sta)
            else:
                q = q.add_entity(site)
                q =q.join(site, site.sta == sensor.sta)
                warnings.warn("No sitechan specified, joining site to sensor on column sta")
        else: 
            raise NameError("No affiliation or sensor table in provided in input query for join to site")
         
    else:
        q = session.query(site)
        if sitechan:
            q = q.add_entity(sitechan)
            q = q.join(sitechan, sitechan.sta==site.sta)

    if stas:
        stas = make_wildcard_list(stas)
        q = q.filter(or_(*[site.sta.like(sta) for sta in stas]))

    if chans:
        if not sitechan:
            raise NameError('Sitechan table required to filter site table by channels')
        stations = make_wildcard_list(chans)
        q = q.filter(or_(*[sitechan.chan.like(chan) for chan in chans]))

    if time_:
        jultime_ = int(time_.strftime('%Y%j'))
        q = q.filter(jultime_ < site.offdate)

    if endtime:
        julendtime = int(endtime.strftime('%Y%j'))
        q = q.filter(julendtime > site.ondate)

    return q

def query_responses(session, sensor, instrument = None, stas = None, chans = None, time_ = None, endtime = None, with_query = None):
    """
    Parameters
    ----------
    session : sqlalchemy.orm.session instance, bound
    sensor : 
    instrument : 
    stas : 
    chans :
    time_ :
    endtime :  
    with_query :

    Returns
    -------
    query
        sdfs
    
    Notes:
    ------
    
    """

    if with_query:
        q = with_query

        sitechan = None
        site = None
        affiliation = None

        for i in q.column_descriptions:
            checkEntity = i['entity']
            if checkEntity._tabletype == 'Sitechan':
                sitechan = checkEntity
            if checkEntity._tabletype == 'Site':
                site = checkEntity
            if checkEntity._tabletype == 'Affiliation':
                affiliation = checkEntity
        
        if sitechan:
            q = q.add_entity(sensor)
            q = q.join(sensor, sitechan.chanid == sensor.chanid)

        elif site:
            q = q.add_entity(sensor)
            q = q.join(sensor, sensor.sta == site.sta)
            warnings.warn("No sitechan specified, joining sensor to site on column sta")
        
        elif affiliation:
            q = q.add_entity(sensor)
            q = q.join(sensor, sensor.sta == affiliation.sta)
            warnings.warn("No site or sitechan specified, joining sensor to affiliation on column sta")
        
        else:
            raise NameError("No table in provided query on which to join the sensor table ")

    else:
        q = session.query(sensor)
    
    if instrument:
        q = q.add_entity(instrument)
        q = q.join(instrument, sensor.inid == instrument.inid)

    if stas:
        stas = make_wildcard_list(stas)
        q = q.filter(or_(*[sensor.sta.like(sta) for sta in stas]))

    if chans:
        chans = make_wildcard_list(chans)
        q = q.filter(or_(*[sensor.chan.like(chan) for chan in chans]))

    if time_:
        q = q.filter(time_.timestamp < sensor.endtime)

    if endtime:
        q = q.filter(endtime.timestamp > sensor.time)


    return q

def assign_unique_net(q, network_name, affiliation_name, pref_nets = None, two_char_code = True, first_available = True, default_net = '__'):
    return 

def check_orphan_stas():
    return
