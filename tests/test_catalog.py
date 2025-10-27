import obspy.core.event as qml
from obspy import UTCDateTime

import pisces.tables.kbcore as kb
import pisces.catalog as cat

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
    observed = cat.catalog(query,
                           resource_prefix=resource_prefix,
                           description='A test catalog',
                       )

    assert observed == expected
