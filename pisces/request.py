"""
request.py

Convenience functions for common queries.

"""
import numpy as np
from sqlalchemy import func, or_
from obspy.core import UTCDateTime, Stream
import obspy.geodetics as geod

from pisces.io.trace import wfdisc2trace


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
            q = q.filter(wfdisc.sta == sta)
        if chan is not None:
            q = q.filter(wfdisc.chan == chan)
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
    mask0 = np.ones(len(records), dtype=np.bool)

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
        mgen = (geod.gps2DistAzimuth(irec.lat, irec.lon, km[0], km[1])[0] \
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
        azgen = (geod.gps2DistAzimuth(irec.lat, irec.lon, km[0], km[1])[1] \
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
        swath=None, stime=None, asquery=False):
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
    t = stime

    q = session.query(Site)

    if stations:
        q = q.filter(Site.sta.in_(sta))

    if nets:
        q = q.join(Affiliation, Affiliation.sta==Site.sta)
        if isinstance(nets, list):
            q = q.filter(Affiliation.net.in_(nets))
        else:
            q = q.filter(func.regexp_like(Affiliation.net, nets))

    if channels:
        q = q.join(Sitechan, Sitechan.sta==Site.sta)
        if isinstance(chans, str):
            #interpret string as regexp
            q = q.filter(func.regexp_like(Sitechan.chan, channnels))
        else:
            q = q.filter(Sitechan.chan.in_(channels))
    
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
        q = q.filter(Arrival.sta.in_(stations))

    if channels:
        q = q.filter(Arrival.chan.in_(channels))

    if phases:
        q = q.filter(Arrival.iphase.in_(phase))

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
        q = q.filter(Arrival.auth.in_(auth))

    if asquery:
        res = q
    else:
        res = q.all()

    return res


def get_waveforms(session, wfdisc, station=None, channel=None, starttime=None,
                  endtime=None, wfids=None, tol=None):
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

    Returns
    -------
    obspy.Stream
        Traces are merged and cut to requested times.

    Raises
    ------
    ValueError
        Returned Stream contains trace start/end times outside of the tolerance.

    """
    # TODO: add evids= option?, use with stawin= option in .execute method?
    # TODO: implement get_arrivals if arrivals=True
    Wfdisc = wfdisc

    st = Stream()
    if wfids:
        station = channel = starttime = endtime = None

    starttime = float(starttime) if starttime is not None else None
    endtime = float(endtime) if endtime is not None else None

    t1_utc = UTCDateTime(starttime) if starttime is not None else None
    t2_utc = UTCDateTime(endtime) if endtime is not None else None

    wfs = get_wfdisc_rows(session, Wfdisc, station, channel, starttime, endtime,
                          wfids=wfids)
    # TODO:
    # Maybe a warning can be fired if the get_waveforms(session, Wfdisc,
    # starttime=t_S, endtime=t_E) function gets data that does not cover
    # starttime endtime (within a tolerance)
    for wf in wfs:
        try:
            tr = wfdisc2trace(wf)
        except IOError:
            # can't read file
            tr = None

        if tr:
            # None utc times will pass through
            tr.trim(t1_utc, t2_utc)
            st.append(tr)
            # TODO: do arrival stuff here?

    if all([tol, starttime, endtime]):
        starttimes, endtimes = zip(*[(t.stats.starttime, t.stats.endtime) for t in st])
        min_t = float(min(starttimes))
        max_t = float(max(endtimes))
        if (abs(min_t - starttime) > tol) or (abs(max_t - endtime) > tol):
            msg = "Trace times are outside of tolerance: {}".format(tol)
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
