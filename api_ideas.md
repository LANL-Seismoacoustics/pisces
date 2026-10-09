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

## a generative database client that can chain meaningful queries
```python

client = DBClient(session_or_config_or_URI, **tables)
# get network-level info for stations containing BH? in a region.
# returns joined sitechan, site, affil, and network
q = client.stations(region=[W, E, S, N], channels='BH?').networks(pref_nets=('II','IU','ISC'))
# get responses for all BH? stations in II
q = client.networks(networks=['II']).stations(channels='BH?').responses()
q = client.events(region=[W, E, S, N], prefor=True).magnitudes(mb=(3, 4)).arrivals(phase='P,S', auth='LANL*')
res = q.all()
```

## an end-to-end workflow using the Pisces query API
```python

from pisces.fdsn import Client
from pisces import inventory, catalog
from pisces.io import read_waveform, read_response

# get broadband waves and responses for stations [20, 80] degrees from events
q = session.query(Site, Sitechan)
try:
    # time gets applied to the lowest-granularity table used in the query, Sitechan here b/c chan keyword was supplied.
    q = filter_stations(q, net='IU', chan='BH_', times=(t1, t2))
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
q = localize(q, region=(W, E, S, N), depth=(dmin, dmax), times=(starttime, endtime))
q = filter_magnitudes(q, magtype='mw', magnitude=(3, 5), netmag=Netmag)


# realize some useful data
cat = catalog(q, resource_id, description=None, comments=None, creation_info=None, auth_priority=('ISC', 'USGS'))

```

## a generative request client class that allows method chaining a-la pandas
```python
from contextlib import contextmanager
class RequestClient:
    def __init__(self, session, **tables):
        # add them to self
        self._event_query = None
        self._station_query = None
        self._waveform_query = None #?
        # or
        self._queries = {} # in methods, add things like: self._queries['event'] = q

    @contextmanager
    def query(self):
        # initially clears queries
        self._event_query = None
        self._station_query = None
        self._waveform_query = None #?
        # or
        self._queries = {}
        try:
            # returns itself inside the context
            yield self
        finally:
            # always clean the instance, even after exceptions
            # Should I do this, if it is cleaned when entering the context?
            # Users may want to inspect the generated queries
            self._event_query = None
            self._station_query = None
            self._waveform_query = None #?
            # or
            self._queries = {}

    def events(self, *stuff, **morestuff):
        if not self._event_query:
            self._event_query = self.session.query(self.tables['event'], self.tables['origin'])
        self._event_query = events.filter_events(self._event_query, *stuff, **morestuff)
        # or
        qe = self._queries.get('event')
        if not qe:
            self._queries['event'] = self.session.query(self.tables['event'], self.tables['origin'])
        self._queries['event'] = events.filter_events(qe, *stuff, **morestuff)


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
            bbox=(-10, 5, 40, 47),
            times=('2009-01-01', '2010-01-01'), #anything UTCDateTime can consume
            depth=(50, 100),
        ).stations(
            channels='BH?,HH*',
        ).distance(
            degrees=(20, 80),
            #or
            kilometers=(50, 300),
            #and/or
            reference=(lat, lon), # if no ref is given, assume event-station distance (spatial join)
        )
        
    st = q.waveforms(
            minlength=84600,
            trim=True,
        )
        
    inv = q.inventory(
        level='response',
    )


# get station magnitudes for events 100-500 degrees from stations
with rclient.query() as q:
    cat = q.stations(
            region=(-10, 5, 40, 47),
            networks='IU',
            channels='HH?',
        ).distance(
            kilometers=(100, 500),
        ).events(
            depth=(10, None),
            mw=(2.0, None),
            # or 
            magnitude={'mw': (2.0, None), ...}
        ).magnitudes(
            level='station/network', # ? not sure about this one
        ).catalog(
            resource_prefix='smi://lanl',
        )


```
