"""
A series of query-building functions

These functions simply add WHERE clauses to an _existing_ query using more convenient syntax.
The incoming query should contain the tables your using in your WHERE clause, or the required
tables should be provided using keywords. If supplied in this way, they'll be used to filter
the result set, but won't be added to the query SELECT statement.


"""
from obspy import UTCDateTime
from sqlalchemy import or_, and_, true

from ..util import _get_entities, range_filters, make_wildcard_list


# TODO: add Origerr to this?
def filter_events(
    query,
    region=None,
    times=None,
    depth=None,
    evid=None,
    orid=None,
    prefor=False,
    auth=None,
    evname=None,
    etype=None,
    **tables
):
    """Filter an event query using Event, Origin tables.

    These filters are primarily geographic and catagorical.  For magnitude filtering,
    Use the `filter_magnitudes` function for magnitude filtering, and filter_arrivals
    for arrivals and amplitudes.

    Parameters
    ----------
    query: sqlalchemy.Query instance
        Includes the required tables for your query (e.g. query = session.query(Event, Origin)),
        otherwise they must be provided as keywords (see below).
    region : tuple [Origin]
        (W, E, S, N) inclusive lat/lon box containing int/float/None(unbounded) degrees
    times : tuple [Origin]
        (starttime, endtime) inclusive range containing int/float/None Unix timestamps
    depth : tuple [Origin]
        (mindepth, maxdepth) inclusive range, in float/int kilometers
    evid : list or tuple of int [Event]
        Event ID number.
    orid : list or tuple of int [Origin]
        Origin ID number.
    prefor : bool [Event, Origin]
        Use only the preferred origin.
    auth : str [Origin]
        Produces an equality clause.
    evname : str [Event]
        Produces a CONTAINS clause (looks for input as a substring).
    etype : str or iterable of str [Origin]
        Two-character KBCore event type(s).  Produces an == clause if it's a string, an "IN" clause
        if it's a list or tuple.
    **tables :
        If a required table isn't in the SELECT of your query, you can provide it
        here as a keyword argument (e.g. event=Event).  It gets used in the filter,
        but isn't included in the final result set (unless it was already in the SELECT).
        If you wish the table included in the result set, use the
        sqlalchemy.orm.Query.add_entity method prior to calling this function.
        e.g. `q = q.add_entity(Event)`

    Joins
    -----
    Event.evid == Origin.evid
    Event.prefor == Origin.orid

    Examples
    --------
    Forgot to include a required table when building query:
    >>> q = session.query(Origin)
    >>> try:
    ... q = filter_events(q, region=(W, E, S, N), prefor=True)
    ... except ValueError:
    ...     # fails b/c Event isn't in the query
    ...     q = filter_events(q, region=(W, E, S, N), prefor=True, event=Event)
    >>> origins = q.all() # a list of preferred Origin instances

    Get a cartesian join of both origins and events
    >>> q = session.query(Origin, Event)
    >>> q = session.query(Origin).add_entity(Event) # equivalent to above
    >>> origins_and_events = filter_events(q, region=(W, E, S, N), prefor=True).all()

    """
    # get desired tables from the query
    Event, Origin = _get_entities(query, "Event", "Origin")

    # override if provided
    Event = tables.get("event", None) or Event
    Origin = tables.get("origin", None) or Origin

    # avoid nonsense inputs
    # TODO: replace with pisces.exc.MissingTableError
    if not any([Event, Origin]):
        msg = "Event or Origin table required."
        raise ValueError(msg)

    if any([times, orid, region, depth]) and not Origin:
        msg = "Origin table required."
        raise ValueError(msg)

    if any([evname, prefor]) and not Event:
        msg = "Event table required."
        raise ValueError(msg)

    if Event and Origin:
        query = query.filter(Event.evid == Origin.evid)
        if prefor:
            query = query.filter(Event.prefor == Origin.orid)

    # Look for a substring of evname
    if evname:
        evname = make_wildcard_list(evname)
        query = query.filter(or_(*[Event.evname.like(n) for n in evname]))

    # prioritize Origin (lowest-granularity table) for common columns.
    evid_auth_table = Origin if Origin else Event
    if evid:
        query = query.filter(evid_auth_table.evid.in_(evid))

    if auth:
        auth = make_wildcard_list(auth)
        query = query.filter(or_(*[evid_auth_table.auth.like(a) for a in auth]))

    if orid:
        query = query.filter(Origin.orid.in_(orid))

    # collect range restrictions on columns
    range_restr = []
    if times:
        t1, t2 = [UTCDateTime(t).timestamp if t is not None else None for t in times]
        range_restr.append((Origin.time, t1, t2))

    if region:
        W, E, S, N = region
        range_restr.append((Origin.lon, W, E))
        range_restr.append((Origin.lat, S, N))

    if depth:
        range_restr.append((Origin.depth, *depth))

    # apply all the range restrictions
    # works even if restrictions is an empty list
    filters = range_filters(*range_restr)
    query = query.filter(*filters)

    if isinstance(etype, (list, tuple)):
        query = query.filter(Origin.etype.in_(etype))
    elif isinstance(etype, str):
        query = query.filter(Origin.etype == etype)

    return query


def filter_magnitudes(
    query,
    net=None,
    sta=None,
    auth=None,
    snr=None,
    amptype=None,
    *,
    netmag=None,
    stamag=None,
    amplitude=None,
    **magnitudes,
):
    """Filter an event query by magnitude range using Origin, Netmag, and/or Stamag tables.

    Supplied tables are joined, and filters are applied to the highest-granularity table they can be:
    Stamag, then Netmag, then Origin. Each magnitude keyword produces an OR clause.

    Parameters
    ----------
    query : sqlalchemy.orm.Query
        Query to filter.
    net : str or iterable of str
        Network code filter; requires Netmag.
    sta : str or iterable of str
        Station code filter; requires Stamag.
    auth : str or iterable of str
        Author filter, applied to Stamag, Netmag, or Origin in that priority order.
    snr : tuple
        ``(min|None, max|None)`` signal-to-noise range; requires Amplitude.
    amptype : str or iterable of str
        Amplitude type filter, wildcards allowed; requires Amplitude.
    netmag, stamag : ORM table class, optional
        Magnitude-domain table to use for filtering when it is not selected by ``query``.
        Event and Origin come from the preceding ``filter_events`` query.
    amplitude : ORM Amplitude table class, optional
        Amplitude table to include or join for result rows. It requires Stamag and joins on
        ``Stamag.ampid == Amplitude.ampid``.
    **magnitudes
        ``magtype=(min|None, max|None)`` filters, for example ``mb=(3.5, 5.5)``. ``all`` applies
        the range to every row-oriented magnitude type. Origin supports only ``mb``, ``ml``, and
        ``ms`` columns; wildcard magnitude types require Netmag or Stamag.

    Joins
    -----
    Origin.orid == Netmag.orid
    Netmag.evid == Event.evid
    Netmag.magid == Stamag.magid
    Origin.orid == Stamag.orid
    Stamag.ampid == Amplitude.ampid

    """
    Event, Origin, Netmag, Stamag, Amplitude = _get_entities(
        query, "Event", "Origin", "Netmag", "Stamag", "Amplitude"
    )
    Netmag = netmag or Netmag
    Stamag = stamag or Stamag
    Amplitude = amplitude or Amplitude

    magtypes = {mag.lower() for mag in magnitudes}
    origin_magtypes = {"mb", "ml", "ms"}
    nonorigin_magtypes = magtypes - origin_magtypes

    if (snr or amptype) and not Amplitude:
        raise ValueError("Amplitude table required for 'snr' and 'amptype' parameters.")
    if Amplitude and not Stamag:
        raise ValueError("Stamag table required for Amplitude rows.")
    if sta and not Stamag:
        raise ValueError("Stamag table required for 'sta' parameter.")
    if net and not Netmag:
        raise ValueError("Netmag table required for 'net' parameter.")
    if nonorigin_magtypes and not (Netmag or Stamag):
        raise ValueError("Netmag or Stamag table required for requested magnitude(s).")
    if not (Origin or Netmag or Stamag):
        raise ValueError("Query must include Origin, Netmag, or Stamag")

    joins = []
    if Stamag and Netmag:
        joins.append(Stamag.magid == Netmag.magid)
    if Netmag and Event:
        joins.append(Netmag.evid == Event.evid)
    if Netmag and Origin:
        joins.append(Netmag.orid == Origin.orid)
    if Stamag and Origin:
        joins.append(Stamag.orid == Origin.orid)
    if Stamag and Amplitude:
        joins.append(Stamag.ampid == Amplitude.ampid)
    query = query.filter(*joins)

    if Stamag:
        Magtable = Stamag
        if sta:
            stas = make_wildcard_list(sta)
            query = query.filter(or_(*(Stamag.sta.like(value) for value in stas)))
    elif Netmag:
        Magtable = Netmag
        if net:
            nets = make_wildcard_list(net)
            query = query.filter(or_(*(Netmag.net.like(value) for value in nets)))
    else:
        Magtable = Origin

    if Magtable is Origin:
        restrictions = [
            (getattr(Origin, magtype), magmin, magmax)
            for magtype, (magmin, magmax) in magnitudes.items()
        ]
        magfilters = range_filters(*restrictions)
    else:
        magfilters = []
        for magtype, (magmin, magmax) in magnitudes.items():
            pattern = make_wildcard_list(magtype)[0]
            type_filter = Magtable.magtype.like(pattern) if pattern != "all" else true()
            range_filter = range_filters((Magtable.magnitude, magmin, magmax))
            magfilters.append(and_(type_filter, *range_filter))

    if magfilters:
        query = query.filter(or_(*magfilters))

    if auth:
        auths = make_wildcard_list(auth)
        query = query.filter(or_(*(Magtable.auth.like(value) for value in auths)))
    if snr:
        query = query.filter(*range_filters((Amplitude.snr, *snr)))
    if amptype:
        amptypes = make_wildcard_list(amptype)
        query = query.filter(or_(*(Amplitude.amptype.like(value) for value in amptypes)))

    return query


def filter_arrivals(query, sta=None, auth=None, times=None, orid=None, phase=None, **tables):
    """
    Filter a query for phase arrival information using Arrival, Assoc

    Parameters
    ----------
    query : SQLAlchemy query object
        Includes any of Arrival, Assoc tables
    sta : str or list [Assoc > Arrival]
    auth : str or list or str [Arrival]
    times : tuple of (starttime, endtime) [Arrival]
        Anything that obspy.UTCDateTime can consume is accepted.
    orid : int or list of int [Assoc]
    phase : str or list of str [Assoc.phase > Arrival.iphase]

    Joins
    -----
    Origin.orid == Assoc.orid
    Assoc.arid == Arrival.arid

    """
    Origin, Arrival, Assoc = _get_entities(query, 'Origin', 'Arrival', 'Assoc')

    # override if provided
    # TODO: These should be required tables, right?
    Arrival = tables.get("arrival", None) or Arrival
    Assoc = tables.get("assoc", None) or Assoc

    # avoid nonsense inputs
    # if not any([Arrival, Assoc]):
    if not (Arrival or Assoc):
        msg = "Arrival or Assoc table required."
        raise ValueError(msg)

    # if any([times, auth]) and not Arrival:
    if (times or auth) and not Arrival:
        msg = "Arrival table required for 'times' and 'auth' parameters."
        raise ValueError(msg)

    # why did I subset orid in Assoc if Origin is required?  did I join it?
    if orid and not Assoc:
        msg = "Assoc table required for 'orid' parameter."
        raise ValueError(msg)

    # do natural joins
    if Origin and Assoc:
        query = query.filter(Origin.orid == Assoc.orid)

    if Arrival and Assoc:
        query = query.filter(Arrival.arid == Assoc.arid)

    # do filters
    if phase:
        phase = make_wildcard_list(phase)
        if Assoc:
            query = query.filter(or_(*[Assoc.phase.like(p) for p in phase]))
        elif Arrival:
            query = query.filter(or_(*[Arrival.iphase.like(p) for p in phase]))

    if sta:
        sta = make_wildcard_list(sta)
        if Assoc:
            query = query.filter(or_(*[Assoc.sta.like(s) for s in sta]))
        elif Arrival:
            query = query.filter(or_(*[Arrival.sta.like(s) for s in sta]))

    if auth:
        auth = make_wildcard_list(auth)
        query = query.filter(or_(*[Arrival.auth.like(a) for a in auth]))

    if orid:
        query = query.filter(Assoc.orid.in_(orid))

    if times:
        t1, t2 = [UTCDateTime(t).timestamp if t is not None else None for t in times]
        time_filter = range_filters((Arrival.time, t1, t2))[0]
        query = query.filter(time_filter)

    return query
