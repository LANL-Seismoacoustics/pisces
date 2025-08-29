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
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import pisces.tables.css3 as css3
import pisces.tables.kbcore as kb
from pisces.fdsn import Client

import pytest




@pytest.fixture(scope='session')
def engine():
    return create_engine('sqlite://')


@pytest.fixture(scope='session')
def tables(engine):
    kb.Site.metadata.create_all(engine) # use the MetaData from any table
    yield
    kb.Site.metadata.drop_all(engine)


@pytest.fixture
def dbsession(engine, tables):
    """Returns an sqlalchemy session, and after the test tears down everything properly."""
    connection = engine.connect()
    # begin the nested transaction
    transaction = connection.begin()
    # use the connection with the already started transaction
    session = Session(bind=connection)

    yield session

    session.close()
    # roll back the broader transaction
    transaction.rollback()
    # put back the connection to the connection pool
    connection.close()


# the "dbsession" test fixture allows your test function to get a clean session
# to an in-memory sqlite database.  You can add test data to it inside your test
# function, and the database will be clean for other tests when the test exits.

def test_get_events_defaults(dbsession):
    origin = kb.Origin(orid=1, evid=2, lat=40, lon=123, time=0, depth=5)
    origin2 = kb.Origin(orid=2, evid=1, lat=42, lon=123)
    origin3 = kb.Origin(orid=3, evid=2, lat=40.5, lon=123)
    event = kb.Event(evid=2, prefor=1)
    netmag = kb.Netmag(evid=2, orid=1, magnitude=4, magtype='mb', magid=1)
    dbsession.add_all([origin, origin2, event, netmag])
    dbsession.commit()

    client = Client(dbsession, origin=kb.Origin, event=kb.Event, netmag=kb.Netmag)
    cat = client.get_events(minlatitude=39, maxlatitude=41, includeallorigins=False)

    expected = qml.Catalog(
        resource_id=cat.resource_id, # a random hash I can't predict, so I just make them match
        creation_info=cat.creation_info, # a specific time I can't predict, so I just make them match
        events=[
            qml.Event(
                resource_id=qml.ResourceIdentifier('smi:local/event/event.evid=2'),
                creation_info=qml.CreationInfo(author='-'),
                event_type='not reported',
                origins=[
                    qml.Origin(
                        resource_id=qml.ResourceIdentifier('smi:local/origin/origin.orid=1'),
                        time=UTCDateTime(0),
                        latitude=40.0,
                        longitude=123,
                        depth=5,
                    ),
                ],
                magnitudes=[
                    qml.Magnitude(
                        resource_id=qml.ResourceIdentifier('smi:local/magnitude/netmag.magid=1'),
                        mag=4.0,
                        magnitude_type='mb',
                        station_count=-1,
                        origin_id=qml.ResourceIdentifier('smi:local/origin/origin.orid=1'),
                    ),
                ],
                preferred_origin_id=qml.ResourceIdentifier('smi:local/origin/origin.orid=1'),
            ),
        ],
    )
    assert cat == expected

    cat = client.get_events(eventid='2')

    assert cat == expected


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



