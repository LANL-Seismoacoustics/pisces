"""
A series of query-building functions with a uniform API

These functions simply add WHERE clauses to an _existing_ query using more convenient syntax.
The incoming query should contain the tables your using in your WHERE clause, or the required
tables should be provided using keywords. If supplied in this way, they'll be used to filter
the result set, but won't be added to the query SELECT statement.

```bash
pisces/
    __init__.py : filter_*, inventory, catalog, stream
    util.py
    crud.py
    request.py @deprecated
    events.py : filter_events, filter_magnitudes, filter_arrivals
    stations.py : filter_networks, filter_stations, filter_responses
    waveforms.py : filter_waveforms
    stream.py : stream
    inventory.py : inventory
    catalog.py : catalog, enum values
    client.py : Client
    fdsnws.py : Client
    commands/
        ...
    schema/
        ...
    tables/
        ...
    io/
        # register various read_* waveform or response functions with their dtype or rsptype string,
        # so that read_waveform/read_response can route to it, each using a standard calling signature
        # and return values.
        __init__.py  # read_waveform, read_response
        sac.py : read_sac, write_sac # + various header conversion functions
        mseed.py : read_mseed, write_mseed
        numpy.py : read_f4, etc...
        waveform.py : read_waveform # registers reader functions
        pazfir.py : read_pazfir
        pazfap.py : read_pazfap
        paziir.py : read_pazfir
        fap.py : read_fap
        fir.py : read_fir
        response.py : read_response # registers reader functions

```

```python

from pisces.fdsn import Client
from pisces import inventory, catalog
from pisces.io import read_waveform, read_response

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
from contextlib import contextmanager
class RequestClient:
    def __init__(self, session, **tables):
        # add them to self
        self._event_query = None
        self._station_query = None
        self._waveform_query = None #?

    @contextmanager
    def query(self):
        self._event_query = None
        self._station_query = None
        self._waveform_query = None #?
        try:
            yield self
        finally:
            self._event_query = None
            self._station_query = None
            self._waveform_query = None #?

    def events(self, *stuff, **morestuff):
        if not self._event_query:
            self._event_query = self.session.query(self.tables['event'], self.tables['origin'])
        self._event_query = events.filter_events(self._event_query, *stuff, **morestuff)

        return self

    def stations(self, *stuff, **morestuff):
        if not self._station_query:
            self._station_query = self.session.query(self.tables['network', 'affiliation', 'site'])

        self._station_query = events.filter_stations(self._station_query, *stuff, **morestuff)

        return self

    def distance(self, *stuff, **morestuff):
        # needs to be called last
        return util.distance(self._event_query, self._station_query, *stuff, **morestuff)

tables = make_tables('origin', 'event', 'arrival', 'assoc', schema='kbcore', owner='global')
rclient = RequestClient(session, **tables)

# get broadband waves and responses for stations [20, 80] degrees from events
with rclient.query() as q:
    q = q.events(
            region=(-10, 5, 40, 47),
            time_=('2009-01-01', '2010-01-01'), #anything UTCDateTime can consume
            depth=(50, 100),
        ).stations(
            channels='BH?,HH?',
        ).distance(
            degrees=(20, 80),
            #or
            kilometers=(50, 300)
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
from obspy import UTCDateTime
from sqlalchemy import or_, and_

from .util import _get_entities, range_filters, make_wildcard_list


# TODO: add Origerr to this?
def filter_events(
    query,
    region=None,
    time_=None,
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
    time_ : tuple [Origin]
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
    etype : str [Origin]
        Two-character event type.  Produces an equality clause.
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

    if any([time_, orid, region, depth]) and not Origin:
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
    if time_:
        t1, t2 = [UTCDateTime(t).timestamp if t is not None else None for t in time_]
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

    if etype:
        query = query.filter(Origin.etype == etype)

    return query


def filter_magnitudes(query, net=None, sta=None, auth=None, **magnitudes_and_tables):
    """
    Filter an event query by magnitude range using Origin, Netmag, and/or Stamag tables.

    Supplied tables are joined, and filters are applied to the highest-granularity table they can be.
    e.g. 'mb' would be filtered in Stamag instead of Netmag, Netmag instead of Origin.

    Each magnitude provided produces an OR clause in SQL.

    Parameters
    ----------
    query : SQLAlchemy query object
        Includes Origin, Netmag, and/or Stamag tables.
    net : str or list of str [Netmag]
        Network code, wildcards allowed. Requires Netmag.
    sta : str or list of str [Stamag]
        Station code, wildcards allowed.  Requies Stamag.
    auth : str or list of str [Stamag > Netmag > Origin]
        Magnitude author, wildcards allowed.  Applied to lowest-granularity table provided.
    **magnitudes_and_tables : [Stamag > Netmag > Origin]
        Magnitudes
        Specify the `magtype=(min|None, max|None)` values for the filter as keyword, 2-tuple pairs,
        e.g. `mb=(3.5, 5.5)`. One special magtype is recognized: `all=(min|None, max|None)` will
        constrain and return all magnitudes. If no range values are provided (e.g. mw=(None, None)),
        all rows with that magtype are returned. Using `all=(None, None)` is the same as providing
        no filter at all. [not yet implemented] Magnitude filters are applied to tables in the
        following priority: Stamag, Netmag, Origin Wildcards are accepted, but they must be provided
        as an expanded dict, like:
        >>> query = query_magnitudes(query, **{'mb': (3, 4), 'mw*': (4, 5.5), 'stamag': Stamag})

        Tables
        If a required ORM table isn't in the SELECT of your query, you can provide it here as a
        keyword argument (e.g. netmag=Netmag). If provided in this way, it won't be returned in the
        result set but is instead just used to filter the result set for the incoming query.
        If you wish a table to be included in the result set, use the
        `sqlalchemy.orm.Query.add_entity` method prior to calling this function.
        e.g. `q = q.add_entity(Stamag)`

    Joins
    -----
    Origin.orid == Netmag.orid
    Netmag.magid == Stamag.magid
    Origin.orid == Stamag.orid

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

    """
    # XXX: if wildcards and only Origin is present, it should/will fail b/c it'll interpret 'm?', for example, as a non-Origin magtype and want to apply the filter to a different table.
    Origin, Netmag, Stamag = _get_entities(query, "Origin", "Netmag", "Stamag")

    # override if provided
    Origin = magnitudes_and_tables.pop("origin", None) or Origin
    Netmag = magnitudes_and_tables.pop("netmag", None) or Netmag
    Stamag = magnitudes_and_tables.pop("stamag", None) or Stamag

    # assumes no extraneous tables/keywords were provided, and all relevent ones are popped off
    magnitudes = magnitudes_and_tables  # for readability/intent
    magtypes = {mag.lower() for mag in magnitudes}
    nonorigin_magtypes = magtypes - {"mb", "ml", "ms"}

    # avoid nonsense inputs
    if sta and not Stamag:
        msg = "Stamag table required for 'sta' parameter."
        raise ValueError(msg)

    if net and not Netmag:
        msg = "Netmag table required for 'net' parameter."
        raise ValueError(msg)

    if nonorigin_magtypes and not any([Netmag, Stamag]):
        msg = "Netmag or Stamag table required for requested magnitude(s)."
        raise ValueError(msg)

    if not any([Origin, Netmag, Stamag]):
        msg = "Query must include Origin, Netmag, or Stamag"
        raise ValueError(msg)

    # do natural joins
    if Stamag and Netmag:
        query = query.filter(Stamag.magid == Netmag.magid)

    if Netmag and Origin:
        query = query.filter(Netmag.orid == Origin.orid)

    if Stamag and Origin:
        query = query.filter(Stamag.orid == Origin.orid)

    # apply mag/auth filters to the highest-granularity table
    # TODO: I don't like how complex this ended up being
    magfilters = []
    if Stamag:
        Magtable = Stamag
        if sta:
            stas = make_wildcard_list(sta)
            query = query.filter(or_(*[Stamag.sta.like(sta) for sta in stas]))
        for magtype, (magmin, magmax) in magnitudes.items():
            magtype = make_wildcard_list(magtype)[0]
            type_filt = Stamag.magtype.like(magtype)
            range_filts = range_filters((Stamag.magnitude, magmin, magmax))
            if range_filts:
                magfilters.append(and_(type_filt, range_filts[0]))
            else:
                magfilters.append(type_filt)

    elif Netmag:
        Magtable = Netmag
        if net:
            nets = make_wildcard_list(net)
            query = query.filter(or_(*[Netmag.net.like(net) for net in nets]))
        for magtype, (magmin, magmax) in magnitudes.items():
            magtype = make_wildcard_list(magtype)[0]
            type_filt = Netmag.magtype.like(magtype)
            range_filts = range_filters((Netmag.magnitude, magmin, magmax))
            if range_filts:
                magfilters.append(and_(type_filt, range_filts[0]))
            else:
                magfilters.append(type_filt)

    elif Origin:
        Magtable = Origin
        restr = []
        for magtype, (magmin, magmax) in magnitudes.items():
            restr.append((getattr(Origin, magtype), magmin, magmax))
        magfilters = range_filters(*restr)

    query = query.filter(or_(*magfilters))

    # apply auth to the highest granularity table
    if auth:
        auths = make_wildcard_list(auth)
        query = query.filter(or_(*[Magtable.auth.like(auth) for auth in auths]))

    return query


def filter_arrivals(query, sta=None, auth=None, time_=None, orid=None, phase=None, **tables):
    """
    Filter a query for phase arrival information using Arrival, Assoc

    Parameters
    ----------
    query : SQLAlchemy query object
        Includes any of Arrival, Assoc tables
    sta : str or list [Assoc > Arrival]
    auth : str or list or str [Arrival]
    time_ : tuple of (starttime, endtime) [Arrival]
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
    Arrival = tables.get("arrival", None) or Arrival
    Assoc = tables.get("assoc", None) or Assoc

    # avoid nonsense inputs
    if not any([Arrival, Assoc]):
        msg = "Arrival or Assoc table required."
        raise ValueError(msg)

    if any([time_, auth]) and not Arrival:
        msg = "Arrival table required for 'time_' and 'auth' parameters."
        raise ValueError(msg)

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

    if time_:
        t1, t2 = [UTCDateTime(t).timestamp if t is not None else None for t in time_]
        time_filter = range_filters((Arrival.time, t1, t2))[0]
        query = query.filter(time_filter)

    return query