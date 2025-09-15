from pisces.schema.css3 import magtype
"""
Tests for fdsn module

Fixtures use from this gist:
https://gist.github.com/kissgyorgy/e2365f25a213de44b9a2

"""
import os
import os.path
import tempfile

import numpy as np
from obspy import UTCDateTime
import obspy.core.event as qml

import pisces as ps
import pisces.tables.kbcore as kb
from pisces.fdsn import Client
from pisces.util import literal_sql

import pytest

def test_get_events_geographic(session):
    """ Geographic tests """
    client = Client(session, origin=kb.Origin, event=kb.Event, netmag=kb.Netmag)

    observed = client.get_events(
        minlatitude=10, maxlatitude=11,
        minlongitude=13, maxlongitude=14,
        mindepth=15,
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
    assert literal_sql(observed) == literal_sql(expected)

def test_get_events_eventid(session):
    """ Specify an event and its preferred origin. """
    client = Client(session, origin=kb.Origin, event=kb.Event, netmag=kb.Netmag)
    observed = client.get_events(eventid=1, includeallorigins=False, asquery=True)
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
    observed = client.get_events(contributor='USGS', eventtype='explosion', asquery=True)
    expected = (
        session.query(kb.Event, kb.Origin, kb.Netmag)
               .filter(kb.Event.evid == kb.Origin.evid)
               .filter(kb.Origin.auth.like('USGS'))
               .filter(kb.Origin.etype.in_(['ec', 'ep', 'ex']))
               .filter(kb.Netmag.evid == kb.Event.evid)
               .filter(kb.Netmag.orid == kb.Origin.orid)
    )
    assert literal_sql(observed) == literal_sql(expected)
    # assert observed.statement.compare(expected.statement)


def test_get_events_magnitudes(session):
    """ Magnitude parameters. """
    client = Client(session, origin=kb.Origin, event=kb.Event, netmag=kb.Netmag)

    # target a magnitude and range
    observed = client.get_events(minmagnitude=3, maxmagnitude=4, magnitudetype='mb', asquery=True)
    expected = (
        session.query(kb.Event, kb.Origin, kb.Netmag)
               .filter(kb.Event.evid == kb.Origin.evid)
               .filter(kb.Netmag.evid == kb.Event.evid)
               .filter(kb.Netmag.orid == kb.Origin.orid)
               .filter(kb.Netmag.magtype.like('mb'))
               .filter(kb.Netmag.magnitude.between(3, 4))
    )
    assert literal_sql(observed) == literal_sql(expected)
    # assert observed.statement.compare(expected.statement)

    # any magnitude, half-range
    observed = client.get_events(minmagnitude=3, asquery=True)
    expected = (
        session.query(kb.Event, kb.Origin, kb.Netmag)
               .filter(kb.Event.evid == kb.Origin.evid)
               .filter(kb.Netmag.evid == kb.Event.evid)
               .filter(kb.Netmag.orid == kb.Origin.orid)
               .filter(kb.Netmag.magnitude >= 3)
    )
    assert literal_sql(observed) == literal_sql(expected)
    # assert observed.statement.compare(expected.statement)

    # error b/c there's no Netmag
    client = Client(session, origin=kb.Origin, event=kb.Event)
    with pytest.raises(ValueError):
        observed = client.get_events(minmagnitude=3, asquery=True)




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
