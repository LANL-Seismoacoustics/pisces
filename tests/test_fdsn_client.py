"""
Tests for fdsn module

Fixtures use from this gist:
https://gist.github.com/kissgyorgy/e2365f25a213de44b9a2

"""
import os
import os.path
import tempfile

import numpy as np
import pytest
from obspy import UTCDateTime
from sqlalchemy import and_, or_

import pisces.tables.kbcore as kb
from pisces.fdsn import Client


def test_get_stations_network(session):
    """Network requests build a filtered Network/Affiliation query."""
    client = Client(
        session,
        network=kb.Network,
        affiliation=kb.Affiliation,
    )

    observed = client.get_stations(network='IU', level='network', asquery=True)
    expected = (
        session.query(kb.Network, kb.Affiliation)
        .filter(kb.Network.net == kb.Affiliation.net)
        .filter(kb.Network.net.like('IU'))
    )

    assert observed.statement.compare(expected.statement)


def test_get_stations_station(session):
    """Station requests join Network, Affiliation, and Site with station filters."""
    client = Client(
        session,
        network=kb.Network,
        affiliation=kb.Affiliation,
        site=kb.Site,
    )

    observed = client.get_stations(network='IU', station='ANMO', asquery=True)
    expected = (
        session.query(kb.Network, kb.Affiliation, kb.Site)
        .filter(kb.Network.net == kb.Affiliation.net)
        .filter(kb.Site.sta == kb.Affiliation.sta)
        .filter(kb.Network.net.like('IU'))
        .filter(kb.Site.sta == kb.Affiliation.sta)
        .filter(kb.Site.sta.like('ANMO'))
    )

    assert observed.statement.compare(expected.statement)


def test_get_stations_channel(session):
    """Channel requests add Sitechan before applying channel filters."""
    client = Client(
        session,
        network=kb.Network,
        affiliation=kb.Affiliation,
        site=kb.Site,
        sitechan=kb.Sitechan,
    )

    observed = client.get_stations(channel='BH?', level='channel', asquery=True)
    expected = (
        session.query(kb.Network, kb.Affiliation, kb.Site)
        .add_entity(kb.Sitechan)
        .filter(kb.Network.net == kb.Affiliation.net)
        .filter(kb.Site.sta == kb.Affiliation.sta)
        .filter(kb.Site.sta == kb.Sitechan.sta)
        .filter(kb.Sitechan.ondate.between(kb.Site.ondate, kb.Site.offdate))
        .filter(kb.Site.sta == kb.Affiliation.sta)
        .filter(kb.Sitechan.chan.like('BH_'))
    )

    assert observed.statement.compare(expected.statement)


def test_get_stations_region(session):
    """Station requests apply rectangular longitude and latitude filters."""
    client = Client(
        session,
        network=kb.Network,
        affiliation=kb.Affiliation,
        site=kb.Site,
    )

    observed = client.get_stations(
        minlongitude=-107,
        maxlongitude=-106,
        minlatitude=34,
        maxlatitude=35,
        asquery=True,
    )
    expected = (
        session.query(kb.Network, kb.Affiliation, kb.Site)
        .filter(kb.Network.net == kb.Affiliation.net)
        .filter(kb.Site.sta == kb.Affiliation.sta)
        .filter(kb.Site.sta == kb.Affiliation.sta)
        .filter(kb.Site.lon.between(-107, -106))        .filter(kb.Site.lat.between(34, 35))
    )

    assert observed.statement.compare(expected.statement)


def test_get_stations_combined_filters(session):
    """Station requests combine network, station, channel, and region filters."""
    client = Client(
        session,
        network=kb.Network,
        affiliation=kb.Affiliation,
        site=kb.Site,
        sitechan=kb.Sitechan,
    )

    observed = client.get_stations(
        network='IU',
        station='ANMO',
        channel='BH?',
        minlongitude=-107,
        maxlongitude=-106,
        minlatitude=34,
        maxlatitude=35,
        level='channel',
        asquery=True,
    )
    expected = (
        session.query(kb.Network, kb.Affiliation, kb.Site)
        .add_entity(kb.Sitechan)
        .filter(kb.Network.net == kb.Affiliation.net)
        .filter(kb.Site.sta == kb.Affiliation.sta)
        .filter(kb.Network.net.like('IU'))
        .filter(kb.Site.sta == kb.Sitechan.sta)
        .filter(kb.Sitechan.ondate.between(kb.Site.ondate, kb.Site.offdate))
        .filter(kb.Site.sta == kb.Affiliation.sta)
        .filter(kb.Site.sta.like('ANMO'))
        .filter(kb.Sitechan.chan.like('BH_'))
        .filter(kb.Site.lon.between(-107, -106))
        .filter(kb.Site.lat.between(34, 35))
    )

    assert observed.statement.compare(expected.statement)


def test_get_stations_response(session):
    """Response requests add response entities and apply response filters."""
    client = Client(
        session,
        network=kb.Network,
        affiliation=kb.Affiliation,
        site=kb.Site,
        sitechan=kb.Sitechan,
        sensor=kb.Sensor,
        instrument=kb.Instrument,
    )

    observed = client.get_stations(
        station='ANMO', channel='BHZ', level='response', asquery=True
    )
    expected = (
        session.query(kb.Network, kb.Affiliation, kb.Site)
        .add_entity(kb.Sitechan)
        .add_entity(kb.Sensor)
        .add_entity(kb.Instrument)
        .filter(kb.Network.net == kb.Affiliation.net)
        .filter(kb.Site.sta == kb.Affiliation.sta)
        .filter(kb.Site.sta == kb.Sitechan.sta)
        .filter(kb.Sitechan.ondate.between(kb.Site.ondate, kb.Site.offdate))
        .filter(kb.Site.sta == kb.Affiliation.sta)
        .filter(kb.Site.sta.like('ANMO'))
        .filter(kb.Sitechan.chan.like('BHZ'))
        .filter(kb.Sensor.inid == kb.Instrument.inid)
        .filter(kb.Sitechan.chanid == kb.Sensor.chanid)
        .filter(kb.Sensor.sta.like('ANMO'))
        .filter(kb.Sensor.chan.like('BHZ'))
    )

    assert observed.statement.compare(expected.statement)


def test_get_stations_missing_tables(session):
    """Station-level requests require Network, Affiliation, and Site tables."""
    client = Client(session, site=kb.Site)

    with pytest.raises(ValueError, match='network, affiliation, site'):
        client.get_stations()


def test_get_stations_invalid_level(session):
    """An unknown station metadata level raises ValueError."""
    client = Client(session, network=kb.Network)

    with pytest.raises(ValueError, match='level must be one of'):
        client.get_stations(level='invalid')


def test_get_stations_radius_ignored(session):
    """Radius arguments are accepted for compatibility but do not alter the query."""
    client = Client(
        session,
        network=kb.Network,
        affiliation=kb.Affiliation,
        site=kb.Site,
    )

    observed = client.get_stations(network='IU', asquery=True)
    with_radius = client.get_stations(
        network='IU',
        latitude=35,
        longitude=-107,
        minradius=1,
        maxradius=2,
        asquery=True,
    )

    assert with_radius.statement.compare(observed.statement)


def test_get_events_geographic(session):
    """ Geographic tests """
    client = Client(session, origin=kb.Origin, event=kb.Event, netmag=kb.Netmag)

    observed = client.get_events(
        minlatitude=10, maxlatitude=11,
        minlongitude=13, maxlongitude=14,
        mindepth=15,
        includeallmagnitudes=True,
        asquery=True
    )
    expected = (
        session.query(kb.Event, kb.Origin, kb.Netmag)
               .filter(kb.Event.evid == kb.Origin.evid)
               .filter(kb.Origin.lon.between(13, 14))
               .filter(kb.Origin.lat.between(10, 11))
               .filter(kb.Origin.depth >= 15)
               .filter(kb.Netmag.evid == kb.Event.evid)
               .filter(kb.Netmag.orid == kb.Origin.orid)
    )
    assert observed.statement.compare(expected.statement)

def test_get_events_eventid(session):
    """ Specify an event and its preferred origin. """
    client = Client(session, origin=kb.Origin, event=kb.Event, netmag=kb.Netmag)
    observed = client.get_events(
        eventid=1, includeallorigins=False, includeallmagnitudes=True, asquery=True
    )
    expected = (
        session.query(kb.Event, kb.Origin, kb.Netmag)
               .filter(kb.Event.evid == kb.Origin.evid)
               .filter(kb.Event.prefor == kb.Origin.orid)
               .filter(kb.Origin.evid.in_([1]))
               .filter(kb.Netmag.evid == kb.Event.evid)
               .filter(kb.Netmag.orid == kb.Origin.orid)
    )
    assert observed.statement.compare(expected.statement)


def test_get_events_misc(session):
    """ Specify events by contributor and event type. """
    client = Client(session, origin=kb.Origin, event=kb.Event, netmag=kb.Netmag)
    observed = client.get_events(
        contributor='USGS', eventtype='explosion', includeallmagnitudes=True, asquery=True
    )
    expected = (
        session.query(kb.Event, kb.Origin, kb.Netmag)
               .filter(kb.Event.evid == kb.Origin.evid)
               .filter(kb.Origin.auth.like('USGS'))
               .filter(kb.Origin.etype.in_(['ec', 'ep', 'ex']))
               .filter(kb.Netmag.evid == kb.Event.evid)
               .filter(kb.Netmag.orid == kb.Origin.orid)
    )
    assert observed.statement.compare(expected.statement)


def test_get_events_magnitudes(session):
    """ Magnitude parameters. """
    client = Client(session, origin=kb.Origin, event=kb.Event, netmag=kb.Netmag)

    # target a magnitude and range
    observed = client.get_events(minmagnitude=3, maxmagnitude=4, magnitudetype='mb', includeallmagnitudes=True, asquery=True)
    expected = (
        session.query(kb.Event, kb.Origin, kb.Netmag)
               .filter(kb.Event.evid == kb.Origin.evid)
               .filter(kb.Netmag.evid == kb.Event.evid)
               .filter(kb.Netmag.orid == kb.Origin.orid)
               .filter(or_(and_(
                   kb.Netmag.magtype.like('mb'),
                   kb.Netmag.magnitude.between(3, 4),
               )))
    )
    assert observed.statement.compare(expected.statement)

    # any magnitude, half-range
    observed = client.get_events(minmagnitude=3, includeallmagnitudes=True, asquery=True)
    expected = (
        session.query(kb.Event, kb.Origin, kb.Netmag)
               .filter(kb.Event.evid == kb.Origin.evid)
               .filter(kb.Netmag.evid == kb.Event.evid)
               .filter(kb.Netmag.orid == kb.Origin.orid)
               .filter(or_(and_(kb.Netmag.magnitude >= 3)))
    )
    assert observed.statement.compare(expected.statement)

    # error b/c there's no Netmag
    client = Client(session, origin=kb.Origin, event=kb.Event)
    with pytest.raises(ValueError):
        observed = client.get_events(minmagnitude=3, includeallmagnitudes=True, asquery=True)




def test_get_waveforms_defaults(dbsession):
    """ If only required parameters are supplied, a simple request returns a result.
    """
    N = 100
    fs = 20
    a = np.arange(N, dtype='<i4')
    # Windows needs the file to not be deleted yet
    with tempfile.NamedTemporaryFile(delete=False) as fp:
        a.tofile(fp)

    t1 = UTCDateTime('2015001')
    t2 = t1 + N/fs
    client = Client(dbsession, wfdisc=kb.Wfdisc, affiliation=kb.Affiliation)
    affil = kb.Affiliation(net='IU', sta='ANMO', time=t1.timestamp-N,
                        endtime=t2.timestamp+N)
    wf = kb.Wfdisc(sta='ANMO', chan='BHZ', time=t1.timestamp, endtime=t2.timestamp,
                samprate=fs, wfid=1, chanid=2, nsamp=N, foff=0, datatype='i4',
                dir=os.path.dirname(fp.name), dfile=os.path.basename(fp.name))
    dbsession.add_all([wf, affil])
    dbsession.commit()

    tr = wf.to_trace()
    st = client.get_waveforms('IU', 'ANMO', '', 'BHZ', t1, t2)

    # finally delete the file
    os.remove(fp.name)

    assert len(st) == 1
    assert (
        st[0].id == tr.id and
        st[0].stats.starttime == tr.stats.starttime and
        st[0].stats.endtime == tr.stats.endtime
    )


def test_get_events_uses_preferred_magnitude(session, eventdata):
    """The FDSN default returns only the preferred mb Netmag per event."""
    client = Client(session, origin=kb.Origin, event=kb.Event, netmag=kb.Netmag)

    observed = client.get_events(eventid=1001)

    assert len(observed.events) == 1
    assert [magnitude.magnitude_type for magnitude in observed.events[0].magnitudes] == ['mb']
