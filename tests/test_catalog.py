import obspy.core.event as qml
from obspy import UTCDateTime

import pisces as ps
import pisces.tables.kbcore as kb
import pisces.catalog as cat
import resource
from pkg_resources import resource_isdir

resource_prefix='smi:local'
qgen = cat.QMLGenerator(resource_prefix=resource_prefix)

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

# skipping remaining QMLGenerator tests b/c they're pretty simple methods.
# Test the more complex functions that use it.

def test_qmltree(eventdata):
    session, data = eventdata

    event1001 = data['event']['evid1001']
    eventkey = cat._key(event1001)

    origin1 = data['origin']['orid1']
    originkey = cat._key(origin1)

    netmag1 = data['netmag']['magid1']
    netmagkey1 = cat._key(netmag1)
    netmag2 = data['netmag']['magid2']
    netmagkey2 = cat._key(netmag2)
    netmag3 = data['netmag']['magid3']
    netmagkey3 = cat._key(netmag3)

    expected = cat._dtree()
    expected[eventkey]['instance'] = event1001
    expected[eventkey]['origins'][originkey]['instance'] = origin1
    expected[eventkey]['origins'][originkey]['netmags'][netmagkey1]['instance'] = netmag1
    expected[eventkey]['origins'][originkey]['netmags'][netmagkey2]['instance'] = netmag2
    expected[eventkey]['origins'][originkey]['netmags'][netmagkey3]['instance'] = netmag3
    # TODO: add arrivals to the test

    query = (
        session.query(kb.Event, kb.Origin, kb.Netmag)
               .filter(kb.Event.evid == kb.Origin.evid)
               .filter(kb.Event.evid == event1001.evid)
               .filter(kb.Origin.orid == kb.Netmag.orid)
    )
    observed = cat.qmltree(query)

    assert observed == expected


def test_catalog(eventdata):
    session, data = eventdata

    event1001 = data['event']['evid1001']
    origin1 = data['origin']['orid1']
    netmag1 = data['netmag']['magid1']
    netmag2 = data['netmag']['magid2']
    netmag3 = data['netmag']['magid3']

    qorigin1 = qml.Origin(
        resource_id=qml.ResourceIdentifier(
            id=f'{resource_prefix}/origin/origin.orid={origin1.orid}'),
        time=UTCDateTime(origin1.time),
        longitude=origin1.lon,
        latitude=origin1.lat,
        depth=origin1.depth,
    )
    qmag1 = qml.Magnitude(
        resource_id=qml.ResourceIdentifier(
                id=f'{resource_prefix}/magnitude/netmag.magid={netmag1.magid}'
            ),
        mag=netmag1.magnitude,
        magnitude_type=netmag1.magtype,
        station_count=netmag1.nsta,
        origin_id=qorigin1.resource_id,
    )
    qmag2 = qml.Magnitude(
        resource_id=qml.ResourceIdentifier(
                id=f'{resource_prefix}/magnitude/netmag.magid={netmag2.magid}'
            ),
        mag=netmag2.magnitude,
        magnitude_type=netmag2.magtype,
        station_count=netmag2.nsta,
        origin_id=qorigin1.resource_id,
    )
    qmag3 = qml.Magnitude(
        resource_id=qml.ResourceIdentifier(
                id=f'{resource_prefix}/magnitude/netmag.magid={netmag3.magid}'
            ),
        mag=netmag3.magnitude,
        magnitude_type=netmag3.magtype,
        station_count=netmag3.nsta,
        origin_id=qorigin1.resource_id,
    )
    qevent = qml.Event(
        resource_id=qml.ResourceIdentifier(
            id=f'{resource_prefix}/event/event.evid={event1001.evid}'
        ),
        creation_info=qml.CreationInfo(author=event1001.auth),
        description=qml.EventDescription(
            text=event1001.evname, type="earthquake name"),
        origins=[qorigin1],
        magnitudes=[qmag1, qmag2, qmag3],
        # amplitudes=None,
        preferred_origin_id=qorigin1.resource_id,
        event_type="explosion",
    )
    expected = qml.Catalog(
        creation_info=qml.CreationInfo(
            author=f'Pisces v{ps.__version__}',
            creation_time=UTCDateTime()
        ),
        resource_id=qml.ResourceIdentifier(
            prefix=f'{resource_prefix}/catalog'
        ),  # uses a uuid after prefix
        description='A test catalog',
        events = [qevent],
    )

    query = (
        session.query(kb.Event, kb.Origin, kb.Netmag)
               .filter(kb.Event.evid == kb.Origin.evid)
               .filter(kb.Event.evid == event1001.evid)
               .filter(kb.Origin.orid == kb.Netmag.orid)
    )
    observed = cat.catalog(query,
                           resource_prefix=resource_prefix,
                           description='A test catalog',
                       )

    assert observed == expected
