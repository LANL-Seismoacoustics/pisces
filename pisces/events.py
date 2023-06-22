"""
A series of query-building functions with a uniform API

These functions simply add WHERE clauses to an _existing_ query using more convenient syntax.
The incoming query should contain the tables your using in your WHERE clause, or the required
tables should be provided using keywords. If supplied in this way, they'll be used to filter
the result set, but won't be added to the query SELECT statement.

```bash
pisces/
    util.py
    crud.py
    request.py @deprecated
    events.py : filter_events, filter_magnitudes, filter_arrivals, catalog
    stations.py : filter_networks, filter_stations, filter_responses, inventory
    waveforms.py : import filter_waveforms, stream
    fdsn.py : Client
    commands/
    schema/
    tables/
    io/
        # register various read_* waveform or response functions with their dtype or rsptype string,
        # so that read_waveform/read_response can route to it, each using a standard calling signature
        # and return values.
        __init__.py  # imports api functions
        sac.py : read_sac, write_sac # + various header conversion functions
        mseed.py : read_mseed, write_mseed
        numpy.py : read_f4, etc...
        waveform.py : read_waveform # registers reader functions
        pazfir.py
        pazfap.py
        paziir.py
        fap.py
        fir.py
        response.py : read_response # registers reader functions

```

```python

from pisces.io.sac import read_sac
from pisces.io.mseed import read_mseed
from pisces.io.response import read_pazfir, read_fap, read_fir, read_paziir, read_pazfap # decide on a common function signature, and use a registry
from pisces.io import read_waveform, read_response
from pisces.events import filter_events, filter_magnitudes, filter_arrivals, catalog
from pisces.stations import filter_networks, filter_stations, filter_responses, inventory
from pisces.waveforms import filter_waveforms, stream
from pisces.request import get_stations, get_events, get_waveforms, ...
from pisces.fdsn import Client
from pisces.client import Client

# get broadband waves and responses for stations [20, 80] degrees from events
q = session.query(Site, Sitechan)
try:
    # time gets applied to the lowest-granularity table used in the query, Sitechan here b/c chan keyword was supplied.
    q = filter_stations(q, net='IU', chan='BH_', time_=(t1, t2))
except ValueError:
    # failed b/c Affiliation isn't in the query
    q = filter_stations(q, net='IU', chan='BH_' affiliation=Affiliation)

# realize some useful research data formats
try:
    q = filter_waveforms(q)
except MissingTableError:
    # Wfdisc wasn't in the query
    q = filter_waveforms(q, wfdisc=Wfdisc)

st = stream(q, filelength=86400, trim=True)

try:
    q = filter_responses(q, instype='something')
except MissingTableError:
    q = filter_responses(q, instype='something', instrument=Instrument, sensor=Sensor)

inv = inventory(q, default_network='__', network_priority=('II', 'IU', 'TA'))


q = session.query(Origin)
q = localize(q, region=(W, E, S, N), depth=(dmin, dmax), time_=(starttime, endtime))
q = filter_magnitudes(q, magtype='mw', magnitude=(3, 5), netmag=Netmag)


# realize some useful data
cat = catalog(q, resource_id, description=None, comments=None, creation_info=None, auth_priority=('ISC', 'USGS'))


...or a request class?
```python
tables = make_tables('origin', 'event', 'arrival', 'assoc', schema='kbcore', owner='global')
rclient = RequestClient(session, **tables)

# get broadband waves and responses for stations [20, 80] degrees from events
with rclient.query() as q:
    q = q.events(
            region=(-10, 5, 40, 47),
            time_=('2009-01-01', '2010-01-01'),
            depth=(50, 100),
            mb=(3.5, 4.5)
        ).stations(
            channels='BH?',
        ).distance(
            degrees=(20, 80),
        )
    st = q.waveforms(
            filelength=84600,
            trim=True,
        )
    inv = q.inventory(
        level='response',
    )


# get station magnitudes for events 100-500 degrees from stations
with rclient.query() as q:
    cat =
        q.stations(
            region=(-10, 5, 40, 47),
            networks='IU',
            channels='HH?',
        ).distance(
            kilometers=(100, 500),
        ).events(
            mw=(2.0, None),
            depth=(10, None),
        ).magnitudes(
            level='station',
        ).catalog()

dbclient.event_query
dbclient.station_query

```

"""


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
    filter method, like query.filter(*filters).

    # e.g.
    >>> range_filters((Origin.lat, -10, 15), (Origin.depth, 25, 80))

    Produces a list containing zero or one filter expressions.
    It's supplied as a list so it can be applied to a query like:
    >>> query.filter(*range_filters(...))
    to produce AND clauses, or
    >>> from sqlalchemy import or_
    >>> query.filter(or_(range_filters(...)))
    to produce OR clauses,
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


def filter_events( query, region=None, time_=None, depth=None, evid=None, orid=None,
    prefor=False, auth=None, name=None, etype=None, **tables
):
    """Filter an event query using Event, Origin tables.

    These filters are primarily geographic and catagorical.  For magnitude filtering,
    use the `filter_magnitudes` function.

    Parameters
    ----------
    query: sqlalchemy.Query instance
        Includes the required tables for your query (e.g. query = session.query(Event, Origin)),
        otherwise they must be provided as keywords (see below).
    region : tuple [Origin]
        (W, E, S, N) inclusive lat/lon box containing int/float/None(unbounded) degrees
    time : tuple [Origin]
        (starttime, endtime) inclusive range containing int/float/None Unix timestamps
    depth : tuple [Origin]
        (mindepth, maxdepth) inclusive range, in float/int kilometers
    evid : list or tuple of ints [Event]
    orid : list or tuple of ints [Origin]
    prefor : bool [Event, Origin]
        Use only the preferred origin.
    auth : str [Origin]
        Produces an equality clause.
    name : str [Event]
        Produces a CONTAINS clause (looks for input as a substring).
    etype : str [Origin]
        Produces an equality clause.
    **tables :
        If a required table isn't in the SELECT of your query, you can provide it
        here as a keyword argument (e.g. event=Event).  It gets used in the filter,
        but isn't included in the final result set (unless it was already in the SELECT).
        If you wish the table included in the result set, use the
        sqlalchemy.orm.Query.add_entity method prior to calling this function.
        e.g. `q = q.add_entity(Event)`

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
    # XXX: add a flag for the 'filter but don't include'
    Event = tables.get("event", None) or Event
    Origin = tables.get("origin", None) or Origin

    # avoid nonsense inputs
    if any([time_, orid, auth, prefor, region, depth]) and not Origin:
        # Origin keywords supplied, but no Origin table present
        # TODO: replace with pisces.exc.MissingTableError
        msg = "Origin table required."
        raise ValueError(msg)

    if any([evid, name, prefor]) and not Event:
        msg = "Event table required."
        raise ValueError(msg)

    if evid and orid:
        msg = "Choose either evid or orid keywords, not both."
        raise ValueError(msg)

    if Event and Origin:
        query = query.filter(Event.evid == Origin.evid)
        if prefor:
            query = query.filter(Event.prefor == Origin.orid)

    # Look for a substring of evname
    if name:
        query = query.filter(Event.evname.contains(name))

    if evid:
        query = query.filter(Event.evid.in_(evid))

    if orid:
        query = query.filter(Origin.orid.in_(orid))

    # collect range restrictions on columns
    range_restr = []
    if time_:
        range_restr.append((Origin.time, *time_))

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

    if etype:
        query = query.filter(Origin.etype == etype)

    if auth:
        query = query.filter(Origin.auth == auth)

    return query


def filter_magnitudes(query, **magnitudes_and_tables):
    """
    Filter an event query by magnitude range using Origin and Netmag or Stamag tables.

    Each magnitude provided produces an OR clause in SQL.

    Parameters
    ----------
    query : SQLAlchemy query object
        Includes Origin[, Netmag, Stamag] tables.
    **magnitudes_and_tables :
        magnitudes
        Specify the magtype=(min, max) values for the filter as keyword, 2-tuple pairs,
        e.g. mb=(3.5, 5.5) . If omitted, all found magnitudes will be returned.
        Wildcards are accepted, but they must be provided as an expanded dict, like:
        >>> {'mb': (3, 4), 'mw*': (4, 5.5)}
        >>> out = query_magnitudes(query, **mags)

        tables
        If a required ORM table isn't in the SELECT of your query, you can provide it here as a
        keyword argument (e.g. netmag=Netmag). If provided in this way, it won't be returned in the
        result set but is instead just used to filter the result set for the incoming query.
        If you wish a table included in the result set, use the `sqlalchemy.orm.Query.add_entity`
        method prior to calling this function.
        e.g. `q = q.add_entity(Stamag)`


    Examples
    --------
    Get filtered Origin results:
    >>> q = session.query(Origin)
    >>> q = events.filter_magnitudes(q, mb=(4.5, 7.5), ms=(4.0, 7.0))

    Get Origin results filtered on Netmag magnitudes:
    >>> q = session.query(Origin)
    >>> try:
    ...     q = events.filter_magnitudes(q, mLg=(2.5, 3.5), mw=(4.0, 6.5))
    ... except ValueError:
    ...     # Netmag table should've been included, so provide it now.
    ...     q = events.filter_magnitudes(q, mLg=(2.5, 3.5), mw=(4.0, 6.5), netmag=Netmag)

    Get

    """
    ORIGINMAGS = {'mb', 'ml', 'ms'}

    # get desired tables from the query
    Origin, Netmag, Stamag = _get_entities(query, "Origin", "Netmag", "Stamag")

    # override if provided
    Origin = magnitudes_and_tables.pop("origin", None) or Origin
    Netmag = magnitudes_and_tables.pop("netmag", None) or Netmag
    Stamag = magnitudes_and_tables.pop("stamag", None) or Stamag

    # assumes no extraneous tables/keywords were provided, and all relevent ones are popped off
    magnitudes = magnitudes_and_tables
    magtypes = {mag.lower() for mag in magnitudes}
    origin_magtypes = magtypes - ORIGINMAGS
    nonorigin_magtypes = magtypes - origin_magtypes

    # use Origin if for any magtypes are found there.
    useOrigin = bool(origin_magtypes)

    # avoid nonsense inputs
    if useOrigin and not Origin:
        msg = "Origin table required for requested magnitudes."
        raise ValueError(msg)

    if not useOrigin and not any([Netmag, Stamag]):
        msg = "Netmag or Stamag table required for requested magnitude(s)."
        raise ValueError(msg)

    constraints = []
    # filter the Origin magnitudes, if any
    for magname in origin_magtypes:
        magrange = magnitudes[magname]
        constraints.append((getattr(Origin, magname), magrange))

def filter_arrivals(query, phases=None, **tables):
    pass
