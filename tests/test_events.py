"""
Tests for the query submodule.

This test module makes heavy use of the .compare method of columns expressions and
query statements, which compares two such objects for equivalence.

"""
import pytest
from obspy import UTCDateTime

from pisces.tables.kbcore import *
from pisces import events

@pytest.fixture(scope='module')
def eventdata(session):
    lat = 40
    lon = 25
    depth = 15
    time_ = UTCDateTime('2000-01-01').timestamp
    data = {
        'event1': Event(evid=1, prefor=1, evname='an important description'),
        'origin1': Origin(orid=1, evid=1, lat=lat, lon=lon, depth=depth, time=time_, auth='auth1'),
        'origin2': Origin(orid=2, evid=1, lat=lat+1, lon=lon+1, depth=depth+1, time=time_+1),
        'event2': Event(evid=2, prefor=3, evname='another description'),
        'origin3': Origin(orid=3, evid=2, lat=lat-5, lon=lon-5, depth=depth-5, time=time_-5, etype='ex', auth='auth2'),
    }
    session.add_all(list(data.values()))
    session.commit()

    yield data, lat, lon, depth, time_

    for item in data.values():
        session.delete(item)

    session.commit()


def test_events_origin(session, eventdata):
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


def test_events_event(session, eventdata):
    d, lat, lon, depth, time_ = eventdata

    q = session.query(Event)

    # evname
    r = events.filter_events(q, name='important').order_by(Event.evid).all()
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


def test_events_origin_event(session, eventdata):
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


def test_events_exceptions(session):
    """ Test expected exceptions. """
    # Origin input with no Origin table
    q = session.query(Event)
    with pytest.raises(ValueError):
        r = events.filter_events(q, orid=[1])

    # Event input with no Origin or Event table
    q = session.query(Site)
    with pytest.raises(ValueError):
        r = events.filter_events(q, evid=[1])

    # both evid and orid specified
    q = session.query(Event, Origin)
    with pytest.raises(ValueError):
        r = events.filter_events(q, evid=[1], orid=[2j])


# def test_magnitudes(session, data):
    # pass