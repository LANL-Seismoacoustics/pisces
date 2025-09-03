"""
Tests for the query submodule.

This test module makes heavy use of the .compare method of columns expressions and
query statements, which compares two such objects for equivalence.

"""
import pytest
from obspy import UTCDateTime
from sqlalchemy import or_

from pisces.tables.kbcore import Event, Origin, Netmag, Stamag, Site
from pisces import events

# print(observed.statement.compile(compile_kwargs={"literal_binds": True}))

lat = 40
lon = 25
depth = 15
time_ = UTCDateTime('2000-01-01').timestamp

def test_filter_events_origin(session):
    """ Tests only on the Origin table. """

    q = session.query(Origin)

    # pass the query through unchanged
    expected = q
    observed = events.filter_events(q)
    assert observed.statement.compare(expected.statement)
    # assert str(expected) == str(observed)

    # full region
    observed = events.filter_events(q, region=(lon-2, lon+2, lat-2, lat+2))
    expected = (
        session.query(Origin)
               .filter(Origin.lon.between(lon-2, lon+2))
               .filter(Origin.lat.between(lat-2, lat+2))
    )
    assert observed.statement.compare(expected.statement)

    # partial region
    observed = events.filter_events(q, region=(None, lon, None, lat))
    expected = (
        session.query(Origin)
               .filter(Origin.lon <= lon)
               .filter(Origin.lat <= lat)
    )
    assert observed.statement.compare(expected.statement)
    # TODO: a region that spans the meridian

    # depth
    observed = events.filter_events(q, depth=(depth-6, depth-4))
    expected = (
            session.query(Origin)
                   .filter(Origin.depth.between(depth-6, depth-4))
    )
    assert observed.statement.compare(expected.statement)

    # orid list
    observed = events.filter_events(q, orid=[1, 2])
    expected = (
        session.query(Origin)
               .filter(Origin.orid.in_([1, 2]))
    )
    assert observed.statement.compare(expected.statement)

    # time
    observed = events.filter_events(q, times=(time_-2, time_+2))
    expected = (
        session.query(Origin)
               .filter(Origin.time.between(time_-2, time_+2))
    )
    assert observed.statement.compare(expected.statement)

    # auth
    observed = events.filter_events(q, auth='auth2')
    expected = (
        session.query(Origin)
               .filter(Origin.auth.like('auth2'))
    )
    assert observed.statement.compare(expected.statement)


def test_filter_events_event(session):
    """ Tests only on the Event table. """

    q = session.query(Event)

    # evname, with two different kinds of wildcard
    observed = events.filter_events(q, evname='*important%')
    expected = (
        session.query(Event)
               .filter(Event.evname.like('%important%'))
    )
    assert observed.statement.compare(expected.statement)

    # evids
    observed = events.filter_events(q, evid=[2])
    expected = (
        session.query(Event)
               .filter(Event.evid.in_([2]))
    )
    assert observed.statement.compare(expected.statement)


def test_filter_events_origin_event(session):
    """ Tests using the Event and Origin tables. """

    q = session.query(Event, Origin)

    # prefor
    observed = events.filter_events(q, prefor=True)
    expected = (
        session.query(Event, Origin)
               .filter(Event.evid == Origin.evid)
               .filter(Origin.orid == Event.prefor)
    )
    assert observed.statement.compare(expected.statement)

    # prefor, but add Event during at calling. it isn't added to the result set
    q = session.query(Origin)
    observed = events.filter_events(q, prefor=True, event=Event)
    expected = (
        session.query(Origin)
               .filter(Event.evid == Origin.evid)
               .filter(Event.prefor == Origin.orid)
    )
    assert observed.statement.compare(expected.statement)


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


def test_filter_magnitudes_origin(session):
    """ Magnitude tests using the Origin table. """

    q = session.query(Origin)

    # magnitudes in origin table
    observed = events.filter_magnitudes(q, ml=(4.5, 5.5), mb=(3, None))
    expected = (
        session.query(Origin)
               .filter(or_(
                        Origin.ml.between(4.5, 5.5), 
                        Origin.mb >= 3
                    )
        )
    )
    assert observed.statement.compare(expected.statement)

    # TODO: filter_magnitudes(q, **{'m?': (1, 2)}) should fail with only Origin

    # auth with wildcard
    observed = events.filter_magnitudes(q, auth='auth?')
    expected = (
        session.query(Origin)
               .filter(Origin.auth.like('auth_'))
    )
    assert observed.statement.compare(expected.statement)


def test_filter_magnitudes_origin_netmag(session):
    """ Magnitude tests using the Origin and Netmag tables. """

    q = session.query(Origin, Netmag)

    # non-origin magnitudes, joined results
    observed = events.filter_magnitudes(q, **{'m?': (5, None)})
    expected = (
        session.query(Origin, Netmag)
               .filter(Netmag.orid == Origin.orid)
               .filter(Netmag.magtype.like('m_'))
               .filter(Netmag.magnitude >= 5)
    )
    assert str(observed) == str(expected)
    # assert observed.statement.compare(expected.statement) # not sure why this isn't working

    # net
    observed = events.filter_magnitudes(q, net='?M')
    expected = (
        session.query(Origin, Netmag)
               .filter(Netmag.orid == Origin.orid)
               .filter(Netmag.net.like('_M'))
    )
    assert observed.statement.compare(expected.statement)

    # auth
    observed = events.filter_magnitudes(q, auth='*D')
    expected = (
        session.query(Origin, Netmag)
               .filter(Netmag.orid == Origin.orid)
               .filter(Netmag.auth.like('%D'))
    )
    assert observed.statement.compare(expected.statement)

    # pop in Netmag to get only Origin results filtered on Netmag
    q = session.query(Origin)
    observed = events.filter_magnitudes(q, ml=(5, None), netmag=Netmag)
    expected = (
        session.query(Origin)
               .filter(Netmag.orid == Origin.orid)
               .filter(Netmag.magtype.like('ml'))
               .filter(Netmag.magnitude >= 5)
    )
    assert str(observed) == str(expected) 
    # assert observed.statement.compare(expected.statement) # not sure why this isn't working


def test_filter_magnitudes_origin_netmag_stamag(session):
    """ Magnitude tests using the Origin, Netmag, and Stamag tables. """

    q = session.query(Origin, Netmag, Stamag)

    # mb from Stamag, joined with the correct Origin, Netmag rows
    observed = events.filter_magnitudes(q, mb=(None, 4))
    expected = (
        session.query(Origin, Netmag, Stamag)
               .filter(Stamag.magid == Netmag.magid)
               .filter(Netmag.orid == Origin.orid)
               .filter(Stamag.orid == Origin.orid)
               .filter(Stamag.magtype.like('mb'))
               .filter(Stamag.magnitude <= 4)
    )
    assert str(observed) == str(expected)
    # assert observed.statement.compare(expected.statement)

    # auth from Stamag
    observed = events.filter_magnitudes(q, auth='*E')
    expected = (
        session.query(Origin, Netmag, Stamag)
               .filter(Stamag.magid == Netmag.magid)
               .filter(Netmag.orid == Origin.orid)
               .filter(Stamag.orid == Origin.orid)
               .filter(Stamag.auth.like('%E'))
    )
    assert observed.statement.compare(expected.statement)

    # sta
    observed = events.filter_magnitudes(q, sta='*2')
    expected = (
        session.query(Origin, Netmag, Stamag)
               .filter(Stamag.magid == Netmag.magid)
               .filter(Netmag.orid == Origin.orid)
               .filter(Stamag.orid == Origin.orid)
               .filter(Stamag.sta.like('%2'))
    )
    assert observed.statement.compare(expected.statement)

    # pop in Netmag
    q = session.query(Origin, Stamag)

    # mb from Stamag, joined with the correct Origin rows
    # we should filter on the Netmag table if it's suppled as a keyword?
    observed = events.filter_magnitudes(q, mb=(None, 4), netmag=Netmag)
    expected = (
        session.query(Origin, Stamag)
               .filter(Stamag.magid == Netmag.magid)
               .filter(Netmag.orid == Origin.orid)
               .filter(Stamag.orid == Origin.orid)
               .filter(Stamag.magtype.like('mb'))
               .filter(Stamag.magnitude <= 4)
    )
    assert str(observed) == str(expected)
    # assert observed.statement.compare(expected.statement) #XXX not sure why this doesn't work

    # pop in Stamag
    # get Origin rows filtered on Stamag magnitudes
    q = session.query(Origin)

    observed = events.filter_magnitudes(q, mb=(None, 4), stamag=Stamag)
    expected = (
        session.query(Origin)
               .filter(Stamag.orid == Origin.orid)
               .filter(Stamag.magtype.like('mb'))
               .filter(Stamag.magnitude <= 4)
    )
    # assert observed.statement.compare(expected.statement) #XXX not sure why this doesn't work
    assert str(observed) == str(expected)


def test_filter_magnitudes_exceptions(session):
    """ Check for expected exceptions. """

    # None of the involved tables are provided
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


# def test_filter_arrivals(session, eventdata):
#     pass


# TODO: Add more "integration" tests
def test_filter_events_magnitudes(session):
    """ Test passing the results of filter_events to filter_magnitudes. """

    # Get preferred origins and mw magnitudes for events in a region
    q = session.query(Origin)
    q = events.filter_events(q, region=(lon-2, lon+2, lat-2, lat+2), prefor=True, event=Event)
    q = q.add_entity(Netmag)
    # points to origin1, netmag3
    # r = events.filter_magnitudes(q, mw=(None, None)).all()
    # assert (
    #     len(r) == 1 and
    #     r[0] == (d['origin1'], d['netmag3'])
    # )
    observed = events.filter_magnitudes(q, mw=(None, None))
    expected = (
        session.query(Origin, Netmag)
               .filter(Event.evid == Origin.evid)
               .filter(Event.prefor == Origin.orid)
               .filter(Origin.lon.between(lon-2, lon+2))
               .filter(Origin.lat.between(lat-2, lat+2))
               .filter(Netmag.orid == Origin.orid)
               .filter(Netmag.magtype.like('mw'))
    )
    assert observed.statement.compare(expected.statement)
    # assert str(observed) == str(expected)
