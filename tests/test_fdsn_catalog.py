import obspy.core.event as qml
from obspy import UTCDateTime

import pisces.tables.kbcore as kb
from pisces.fdsn.catalog import catalog, QMLGenerator

resource_prefix='smi:local'
qgen = QMLGenerator(resource_prefix=resource_prefix)

def test_QMLGenerator_event(eventdata):
    session, data = eventdata
    event = data['event']['evid1001']

    expected = qml.Event(
        resource_id=qml.ResourceIdentifier(
            id=f'{resource_prefix}/event/event.evid={event.evid}'
        ),
        creation_info=qml.CreationInfo(author=event.auth),
        description=qml.EventDescription(
            text=event.evname, type="earthquake name"),
    )
    observed = qgen.event(event)
    assert observed == expected


def test_QMLGenerator_origin(eventdata):
    session, data = eventdata
    origin = data['origin']['orid1']

    expected = qml.Origin(
        resource_id=qml.ResourceIdentifier(
            id=f'{resource_prefix}/origin/origin.orid={origin.orid}'),
        time=UTCDateTime(origin.time),
        longitude=origin.lon,
        latitude=origin.lat,
        depth=origin.depth,
    )
    observed = qgen.origin(origin)
    assert observed == expected

def test_QMLGenerator_amplitude(eventdata):
    """Arrival amplitudes convert from CSS nanometers to QuakeML meters."""
    _, data = eventdata
    arrival = data['arrival']['ANMO1']
    expected_amplitude = arrival.amp  # load the ORM row before _denull expunges it

    observed = qgen.amplitude(arrival)

    assert observed.generic_amplitude == expected_amplitude * 1e-9
    assert observed.unit == 'm'


# skipping remaining QMLGenerator tests b/c they're pretty simple methods.
# Test the more complex functions that use it.

def test_catalog_deduplicates_redundant_rows(eventdata):
    # One event/origin repeated across rows (once per netmag) must produce a single QuakeML
    # Event and Origin, with one Magnitude per distinct Netmag row.
    session, data = eventdata

    event1001 = data['event']['evid1001']
    netmags = [data['netmag'][magid] for magid in ('magid1', 'magid2', 'magid3')]

    query = (
        session.query(kb.Event, kb.Origin, kb.Netmag)
               .filter(kb.Event.evid == kb.Origin.evid)
               .filter(kb.Event.evid == event1001.evid)
               .filter(kb.Origin.orid == kb.Netmag.orid)
    )
    # the query really is redundant: one row per netmag, all with the same event/origin
    assert query.count() == len(netmags)

    observed = catalog(query, resource_prefix=resource_prefix)

    assert len(observed.events) == 1
    qevent = observed.events[0]
    assert len(qevent.origins) == 1
    assert len(qevent.magnitudes) == len(netmags)
    assert {mag.mag for mag in qevent.magnitudes} == {nm.magnitude for nm in netmags}
    # every magnitude points at the one origin
    assert {mag.origin_id for mag in qevent.magnitudes} == {qevent.origins[0].resource_id}


def test_catalog(eventdata, eventqml):
    session, data = eventdata
    expected = eventqml

    event1001 = data['event']['evid1001']

    query = (
        session.query(kb.Event, kb.Origin, kb.Netmag)
               .filter(kb.Event.evid == kb.Origin.evid)
               .filter(kb.Event.evid == event1001.evid)
               .filter(kb.Origin.orid == kb.Netmag.orid)
    )
    observed = catalog(query,
                           resource_prefix=resource_prefix,
                           description='A test catalog',
                       )

    assert observed == expected


def test_catalog_pairs_assocs_with_same_row_arrivals(eventdata):
    # Assoc and Arrival arrive together on a row, and each QuakeML Arrival's pick_id must point at
    # the Pick built from *that same row's* Arrival.
    session, data = eventdata

    event1001 = data['event']['evid1001']

    query = (
        session.query(kb.Event, kb.Origin, kb.Assoc, kb.Arrival)
               .filter(kb.Event.evid == kb.Origin.evid)
               .filter(kb.Event.evid == event1001.evid)
               .filter(kb.Origin.orid == kb.Assoc.orid)
               .filter(kb.Assoc.arid == kb.Arrival.arid)
    )
    rows = query.all()
    assert rows, "fixture should produce assoc/arrival rows"

    observed = catalog(query, resource_prefix=resource_prefix)

    qevent = observed.events[0]
    qorigin = qevent.origins[0]
    assert len(qorigin.arrivals) == len(rows)
    assert len(qevent.picks) == len(rows)

    # map each pick's resource_id to the station it came from, then confirm every QuakeML Arrival's
    # pick_id resolves to the pick for the same station/phase as its source Assoc row.
    pick_station = {pick.resource_id: pick.waveform_id.station_code for pick in qevent.picks}
    for qarrival, row in zip(qorigin.arrivals, rows):
        assoc = getattr(row, kb.Assoc.__name__)
        assert qarrival.pick_id is not None
        assert pick_station[qarrival.pick_id] == assoc.sta


def test_catalog_adds_station_magnitudes_and_contributions(eventdata):
    """Stamags link same-row Netmags and Arrival-derived amplitudes."""
    session, data = eventdata
    event = data['event']['evid1001']
    netmag = data['netmag']['magid1']

    query = (
        session.query(kb.Event, kb.Origin, kb.Netmag, kb.Stamag, kb.Arrival)
        .filter(kb.Event.evid == kb.Origin.evid)
        .filter(kb.Event.evid == event.evid)
        .filter(kb.Origin.orid == kb.Netmag.orid)
        .filter(kb.Netmag.magid == netmag.magid)
        .filter(kb.Stamag.magid == kb.Netmag.magid)
        .filter(kb.Arrival.arid == kb.Stamag.arid)
    )

    observed = catalog(query, resource_prefix=resource_prefix)
    qevent = observed.events[0]
    qmagnitude = qevent.magnitudes[0]

    assert len(qevent.station_magnitudes) == 2
    assert {stamag.mag for stamag in qevent.station_magnitudes} == {5.3, 5.1}
    assert {stamag.amplitude_id for stamag in qevent.station_magnitudes} == {
        amplitude.resource_id for amplitude in qevent.amplitudes
    }
    assert len(qmagnitude.station_magnitude_contributions) == 2
    assert {contribution.weight for contribution in qmagnitude.station_magnitude_contributions} == {1.0}


def test_catalog_uses_database_amplitudes_when_selected(eventdata):
    """Selected Amplitude rows replace Arrival-derived amplitudes and link by ampid."""
    session, data = eventdata
    event = data['event']['evid1001']
    netmag = data['netmag']['magid1']
    amplitude = data['amplitude']['ampid1']

    query = (
        session.query(kb.Event, kb.Origin, kb.Netmag, kb.Stamag, kb.Amplitude)
        .filter(kb.Event.evid == kb.Origin.evid)
        .filter(kb.Event.evid == event.evid)
        .filter(kb.Origin.orid == kb.Netmag.orid)
        .filter(kb.Netmag.magid == netmag.magid)
        .filter(kb.Stamag.magid == kb.Netmag.magid)
        .filter(kb.Stamag.ampid == kb.Amplitude.ampid)
        .filter(kb.Amplitude.ampid == amplitude.ampid)
    )

    observed = catalog(query, resource_prefix=resource_prefix)
    qevent = observed.events[0]

    assert len(qevent.amplitudes) == 1
    qamplitude = qevent.amplitudes[0]
    assert str(qamplitude.resource_id) == f'{resource_prefix}/amplitude/amplitude.ampid=1'
    assert qamplitude.generic_amplitude == 9000.0e-9
    assert qevent.station_magnitudes[0].amplitude_id == qamplitude.resource_id



def test_catalog_marks_preferred_magnitude(eventdata):
    """The preferred-origin mb magnitude wins the fixed priority order."""
    session, data = eventdata
    event = data['event']['evid1001']

    query = (
        session.query(kb.Event, kb.Origin, kb.Netmag)
        .filter(kb.Event.evid == kb.Origin.evid)
        .filter(kb.Event.evid == event.evid)
        .filter(kb.Origin.orid == kb.Netmag.orid)
    )

    observed = catalog(query, resource_prefix=resource_prefix)

    assert observed.events[0].preferred_magnitude_id == qml.ResourceIdentifier(
        id=f'{resource_prefix}/magnitude/netmag.magid=1'
    )
