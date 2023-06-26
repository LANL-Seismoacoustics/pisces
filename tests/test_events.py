"""
Tests for the query submodule.

This test module makes heavy use of the .compare method of columns expressions and
query statements, which compares two such objects for equivalence.

"""
import pytest
from obspy import UTCDateTime

from pisces.tables.kbcore import *
from pisces import events

# for scope='module' these database rows are added to a temp database once for this whole file,
# then removed at the end. Not sure that's necessary.
@pytest.fixture(scope='module')
def eventdata(session):
    lat = 40
    lon = 25
    depth = 15
    time_ = UTCDateTime('2000-01-01').timestamp
    # event stuff
    data = {
        'event1': Event(evid=1, prefor=1, evname='an important description'),
        'origin1': Origin(orid=1, evid=1, lat=lat, lon=lon, depth=depth, time=time_, auth='auth1', mb=4.1, mbid=1, ms=5, ml=6, mlid=2),
        'origin2': Origin(orid=2, evid=1, lat=lat+1, lon=lon+1, depth=depth+1, time=time_+1, ml=5),
        'event2': Event(evid=2, prefor=3, evname='another description'),
        'origin3': Origin(orid=3, evid=2, lat=lat-5, lon=lon-5, depth=depth-5, time=time_-5, etype='ex', auth='auth2', mb=2, ms=3, ml=4),
    }
    # magnitude stuff
    data.update({
        'netmag1': Netmag(net='IM', orid=1, evid=1, magtype='mb', magnitude=4, magid=1, auth='ISC'),
        'netmag2': Netmag(net='IN', orid=2, evid=1, magtype='ml', magnitude=6, magid=2, auth='ISD'),
        'netmag3': Netmag(net='IO', orid=1, evid=1, magtype='mw', magnitude=4, magid=3, auth='ISC'),
        'stamag1': Stamag(sta='sta1', arid=1, magtype='ml', magnitude=4.1, magid=2, orid=1, auth='ISD'),
        'stamag2': Stamag(sta='sta2', arid=2, magtype='ml', magnitude=3.9, magid=2, orid=2, auth='ISD'),
        'stamag3': Stamag(sta='sta1', arid=3, magtype='mb', magnitude=3.9, magid=1, orid=1, auth='ISE'),
    })

    session.add_all(list(data.values()))
    session.commit()

    yield data, lat, lon, depth, time_

    for item in data.values():
        session.delete(item)

    session.commit()


def test_filter_events_origin(session, eventdata):
    d, lat, lon, depth, time_ = eventdata

    q = session.query(Origin)

    # pass the query through unchanged
    expected = q
    observed = events.filter_events(q)
    assert observed.statement.compare(expected.statement)
    # assert str(expected) == str(observed)

    # full region
    r = events.filter_events(q, region=(lon-2, lon+2, lat-2, lat+2)).order_by(Origin.orid).all()
    assert (
        len(r) == 2 and
        r[0] == d['origin1'] and
        r[1] == d['origin2']
    )

    # partial region
    r = events.filter_events(q, region=(None, lon, None, lat)).order_by(Origin.orid).all()
    assert (
        len(r) == 2 and
        r[0] == d['origin1'] and
        r[1] == d['origin3']
    )
    # TODO: a region that spans the meridian

    # depth
    r = events.filter_events(q, depth=(depth-6, depth-4)).all()
    assert (
        len(r) == 1 and
        r[0] == d['origin3']
    )

    # orid list
    r = events.filter_events(q, orid=[1, 2]).order_by(Origin.orid).all()
    assert (
        len(r) == 2 and
        r[0] == d['origin1'] and
        r[1] == d['origin2']
    )

    # time
    r = events.filter_events(q, time_=(time_-2, time_+2)).order_by(Origin.orid).all()
    assert (
        len(r) == 2 and
        r[0] == d['origin1'] and
        r[1] == d['origin2']
    )

    # auth
    r = events.filter_events(q, auth='auth2').order_by(Origin.orid).all()
    assert (
        len(r) == 1 and
        r[0] == d['origin3']
    )


def test_filter_events_event(session, eventdata):
    d, lat, lon, depth, time_ = eventdata

    q = session.query(Event)

    # evname, with two different kinds of wildcard
    r = events.filter_events(q, evname='*important%').order_by(Event.evid).all()
    assert (
        len(r) == 1 and
        r[0] == d['event1']
    )

    # evids
    r = events.filter_events(q, evid=[2]).order_by(Event.evid).all()
    assert (
        len(r) == 1 and
        r[0] == d['event2']
    )


def test_filter_events_origin_event(session, eventdata):
    d, lat, lon, depth, time_ = eventdata

    q = session.query(Event, Origin)

    # prefor
    r = events.filter_events(q, prefor=True).order_by(Event.evid).all()
    assert (
        len(r) == 2 and
        r[0] == (d['event1'], d['origin1']) and
        r[1] == (d['event2'], d['origin3'])
    )
    # prefor, but add Event during at calling.
    # it isn't added to the result set
    q = session.query(Origin)
    r = events.filter_events(q, prefor=True, event=Event).order_by(Event.evid).all()
    assert (
        len(r) == 2 and
        r[0] == d['origin1'] and
        r[1] == d['origin3']
    )


def test_filter_events_exceptions(session):
    """ Test expected exceptions. """

    # Origin input with no Origin table
    q = session.query(Event)
    with pytest.raises(ValueError):
        r = events.filter_events(q, orid=[1])

    # Event input with no Origin or Event table
    q = session.query(Site)
    with pytest.raises(ValueError):
        r = events.filter_events(q, evid=[1])


def test_filter_magnitudes_origin(session, eventdata):
    d, *_ = eventdata

    q = session.query(Origin)

    # origin magnitudes
    r = events.filter_magnitudes(q, ml=(4.5, 5.5), mb=(3, None)).order_by(Origin.orid).all()
    assert (
        len(r) == 2 and
        r[0] == d['origin1'] and
        r[1] == d['origin2']
    )

    # TODO: filter_magnitudes(q, **{'m?': (1, 2)}) should fail with only Origin

    # auth
    r = events.filter_magnitudes(q, auth='auth?').order_by(Origin.orid).all()
    assert (
        len(r) == 2 and
        r[0] == d['origin1'] and
        r[1] == d['origin3']
    )

def test_filter_magnitudes_origin_netmag(session, eventdata):
    d, *_ = eventdata

    q = session.query(Origin, Netmag)

    # non-origin magnitudes, joined results
    r = events.filter_magnitudes(q, **{'m?': (5, None)}).order_by(Origin.orid).all()
    assert (
        len(r) == 1 and
        r[0] == (d['origin2'], d['netmag2'])
    )

    # net
    r = events.filter_magnitudes(q, net='?M').order_by(Origin.orid).all()
    assert (
        len(r) == 1 and
        r[0] == (d['origin1'], d['netmag1'])
    )

    # auth
    r = events.filter_magnitudes(q, auth='*D').order_by(Origin.orid).all()
    assert (
        len(r) == 1 and
        r[0] == (d['origin2'], d['netmag2'])
    )

    # pop in Netmag to get only Origin results filtered on Netmag
    q = session.query(Origin)
    r = events.filter_magnitudes(q, ml=(5, None), netmag=Netmag).order_by(Origin.orid).all()
    assert (
        len(r) == 1 and
        r[0] == d['origin2']
    )


def test_filter_magnitudes_origin_netmag_stamag(session, eventdata):
    d, *_ = eventdata

    q = session.query(Origin, Netmag, Stamag)

    # mb from Stamag, joined with the correct Origin, Netmag rows
    r = events.filter_magnitudes(q, mb=(None, 4)).order_by(Origin.orid).all()
    assert (
        len(r) == 1 and
        r[0] == (d['origin1'], d['netmag1'], d['stamag3'])
    )

    # auth from Stamag
    r = events.filter_magnitudes(q, auth='*E').order_by(Origin.orid).all()
    assert (
        len(r) == 1 and
        r[0] == (d['origin1'], d['netmag1'], d['stamag3'])
    )

    # sta
    r = events.filter_magnitudes(q, sta='*2').order_by(Origin.orid).all()
    assert (
        len(r) == 1 and
        r[0] == (d['origin2'], d['netmag2'], d['stamag2'])
    )

    # pop in Netmag
    q = session.query(Origin, Stamag)

    # mb from Stamag, joined with the correct Origin rows
    r = events.filter_magnitudes(q, mb=(None, 4), netmag=Netmag).order_by(Origin.orid).all()
    assert (
        len(r) == 1 and
        r[0] == (d['origin1'], d['stamag3'])
    )

    # pop in Stamag
    # get Origin rows filtered on Stamag magnitudes
    q = session.query(Origin)

    r = events.filter_magnitudes(q, mb=(None, 4), stamag=Stamag).order_by(Origin.orid).all()
    assert (
        len(r) == 1 and
        r[0] == d['origin1']
    )


def test_filter_magnitudes_exceptions(session, eventdata):
    """ Check for expected exceptions. """
    d, *_ = eventdata

    # None of the involved tables provided
    q = session.query(Site)
    with pytest.raises(ValueError):
        q = events.filter_magnitudes(q, mb=(4, 5))

    # Netmag not provided for Netmag parameters
    q = session.query(Origin)
    with pytest.raises(ValueError):
        q = events.filter_magnitudes(q, net='IM')

    # Stamag/Netmag not provided for non-Origin magnitude
    with pytest.raises(ValueError):
        q = events.filter_magnitudes(q, mw=(3, 5))

    with pytest.raises(ValueError):
        q = events.filter_magnitudes(q, sta='sta1')


def test_filter_arrivals(session, eventdata):
    pass


# TODO: Add more "integration" tests eventually
def test_filter_events_magnitudes(session, eventdata):
    """ Test passing the results of filter_events to filter_magnitudes. """
    d, lat, lon, depth, time_ = eventdata

    # Get preferred origins and mw magnitudes for events in a region
    q = session.query(Origin, Netmag)
    q = events.filter_events(q, region=(lon-2, lon+2, lat-2, lat+2), prefor=True, event=Event)
    # points to origin1, netmag3
    r = events.filter_magnitudes(q, mw=(None, None)).all()
    assert (
        len(r) == 1 and
        r[0] == (d['origin1'], d['netmag3'])
    )
