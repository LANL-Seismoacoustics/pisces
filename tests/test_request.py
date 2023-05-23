from textwrap import dedent

from obspy import UTCDateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

import pisces.request as req
from pisces.tables.kbcore import *

engine = create_engine('sqlite:///:memory:', echo=False)
Session = sessionmaker(bind=engine)


@pytest.fixture(scope='module')
def session():
    """Returns an sqlalchemy session, and after the test, it tears down everything properly."""
    s = Session()
    # Pick a table to access the metadata containing all tables, and create them
    Affiliation.metadata.create_all(s.bind)
    yield s
    s.close()
    Affiliation.metadata.drop_all(s.bind)

@pytest.fixture(scope='function')
def get_stations_data(session):
    """ Data in support of anything in the get_stations family of queries

    This includes network, station, and response queries. 
    
    """
    # test cases should include:
    # - an array within one network (IM NVAR)
    # - a station with multiple site entries in one network (IU ANMO)
    # - a station with multiple network affiliations (IU|SR ANMO)

    # SR|ANMO|34.946201|-106.456703|1740.0||1974-08-28T00:00:00.0000|1989-08-30T00:00:00.0000
    # IU|ANMO|34.9459|-106.4572|1850.0||1989-08-29T00:00:00.0000|2000-10-19T16:00:00.0000
    # IU|ANMO|34.9502|-106.4602|1839.0||2000-10-19T16:00:00.0000|2002-11-19T21:07:00.0000
    # IU|ANMO|34.94591|-106.4572|1820.0||2002-11-19T21:07:00.0000|
    # IM|NV32|38.334301|-118.2995|1829.0||1970-01-24T00:00:00.0000|2008-01-08T17:59:00.0000
    # IM|NV33|38.485001|-118.418297|1920.0||1970-01-24T00:00:00.0000|2008-01-08T17:59:00.0000
    # IM|NVAR|38.4296|-118.303596|2041.6|1972-01-03T00:00:00.0000|

    IU = Network(net='IU')
    SR = Network(net='SR')
    IM = Network(net='IM')

    ANMO_0 = Site(sta='ANMO', ondate=jdate('1974-11-19'), offdate=jdate('1989-08-30')) # SR
    ANMO_1 = Site(sta='ANMO', ondate=jdate('1989-08-29'), offdate=jdate('2000-10-19')) # IU
    ANMO_2 = Site(sta='ANMO', ondate=jdate('2000-10-20'), offdate=jdate('2002-11-19')) # IU
    NV32 = Site(sta='NV32', ondate=jdate('1970-01-24'), offdate=jdate('2008-01-08')) # IM
    NV33 = Site(sta='NV33', ondate=jdate('1970-01-24'), offdate=jdate('2008-01-08')) # IM

    # just use station ondate/offdate as affiliation time/endtime
    SR_ANMO_0 = Affiliation(net=SR.net, sta=ANMO_0.sta, time=jdate2epoch(ANMO_0.ondate), endtime=jdate2epoch(ANMO_0.offdate))
    IU_ANMO_1 = Affiliation(net=IU.net, sta=ANMO_1.sta, time=jdate2epoch(ANMO_1.ondate), endtime=jdate2epoch(ANMO_1.offdate))
    IU_ANMO_2 = Affiliation(net=IU.net, sta=ANMO_2.sta, time=jdate2epoch(ANMO_2.ondate), endtime=jdate2epoch(ANMO_2.offdate))
    IM_NV32 = Affiliation(net=IM.net, sta=NV32.sta, time=jdate2epoch(NV32.ondate), endtime=jdate2epoch(NV32.offdate))
    IM_NV33 = Affiliation(net=IM.net, sta=NV33.sta)
    
    data = {
        'IU': IU,
        'SR': SR,
        'IM': IM,
        'ANMO_0': ANMO_0,
        'ANMO_1': ANMO_1,
        'ANMO_2': ANMO_2,
        'NV32': NV32,
        'NV33': NV33,
        'SR_ANMO_0': SR_ANMO_0,
        'IU_ANMO_1': IU_ANMO_1,
        'IU_ANMO_2': IU_ANMO_2,
        'IM_NV32': IM_NV32,
        'IM_NV33': IM_NV33,
    }
    session.add_all(data.values())
    session.commit()
    
    yield data
    
    for item in data.values():
        session.delete(item)

    session.commit()
    

def jdate(indate: str) -> int:
    # '2002-11-09' -> 2002323
    return int(UTCDateTime(indate).strftime('%Y%j'))

def jdate2epoch(jdate: int) -> float:
    # 2002323 -> 1037668325.0
    return UTCDateTime.strptime(str(jdate), '%Y%j').timestamp
    

def test_query_network(session, get_stations_data):
    d = get_stations_data
    
    # All networks are returned if none specified 
    # expected = [
    #     Network(net='IM'),
    #     Network(net='IU'),
    #     Network(net='SR'),
    # ]
    out = req.query_network(session, Network).order_by(Network.net).all()
    assert out == [d['IM'], d['IU'], d['SR']]

    # correct network is returned if provided
    # expected = [
    #     Network(net='IU')
    # ]
    out = req.query_network(session, Network, nets=['IU']).all()
    assert out == [d['IU']]

    # Affiliation information is present if provided
    # expected = [
    #     (Network(net='IU'), Affiliation(net='IU', sta='ANMO', time=620352000.0)),
    #     (Network(net='IU'), Affiliation(net='IU', sta='ANMO', time=972000000.0)),
    # ]
    q = req.query_network(session, Network, nets=['IU'], affiliation=Affiliation)
    out = q.order_by(Affiliation.time).all()
    assert (
        len(out) == 2 and # two results returned
        len(out[0]) == 2 and # two entities in each result
        out[0] == (d['IU'], d['IU_ANMO_1']) and
        out[1] == (d['IU'], d['IU_ANMO_2'])
    )

    # only one Network for one specific station is included when stas specified
    # and a station is only associated with one network.
    # expected = [
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV33', time=-9999999999.999))
    # ]
    out = req.query_network(session, Network, affiliation=Affiliation, stas=['NV33']).all()
    assert (
        len(out) == 1 and
        out[0] == (d['IM'], d['IM_NV33'])
    )

    with pytest.raises(NameError):
        # without Affiliation provided, stas should fail
        out = req.query_network(session, Network, stas=['NV33']).all()

    # two Networks for one specific station is included when stas specified
    # and a station is associated with two networks.
    # expected = [
    #     (Network(net='SR'), Affiliation(net='SR', sta='ANMO', time=...)),
    #     (Network(net='IU'), Affiliation(net='IU', sta='ANMO', time=620352000.0)),
    #     (Network(net='IU'), Affiliation(net='IU', sta='ANMO', time=972000000.0)),
    # ]
    q = req.query_network(session, Network, affiliation=Affiliation, stas=['ANMO'])
    out = q.order_by(Affiliation.time).all()
    assert (
        len(out) == 3 and
        out[0] == (d['SR'], d['SR_ANMO_0']) and
        out[1] == (d['IU'], d['IU_ANMO_1']) and
        out[2] == (d['IU'], d['IU_ANMO_2'])
    )

    # wildcarded array elements are returned properly
    # expected = [
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV32', time=-9999999999.999))
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV33', time=-9999999999.999))
    # ]
    q = req.query_network(session, Network, affiliation=Affiliation, stas=['NV*'])
    out = q.order_by(Affiliation.sta).all()
    assert (
        len(out) == 2 and
        out[0] == (d['IM'], d['IM_NV32']) and
        out[1] == (d['IM'], d['IM_NV33'])
    )

    # get results where network affiliation ends after time_
    # expected = [
    #     (Network(net='IU'), Affiliation(net='IU', sta='ANMO', time=972000000.0)),
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV32', time=1987200.0)),
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV33', time=-9999999999.999)),
    # ]
    # TODO: Is this how time_ is meant to work?
    time_= UTCDateTime('2001-01-01') 
    q = req.query_network(session, Network, affiliation=Affiliation, time_=time_)
    out = q.order_by(Affiliation.endtime).all()
    assert (
        len(out) == 3 and
        out[0] == (d['IU'], d['IU_ANMO_2']) and
        out[1] == (d['IM'], d['IM_NV32']) and
        out[2] == (d['IM'], d['IM_NV33'])
    )
    with pytest.raises(NameError):
        # without Affiliation provided, time queries should fail
        out = req.query_network(session, Network, time_=time_).all()
        

    # get results where network affiliation.time < endtime
    # expected = [
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV33', time=-9999999999.999)),
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV32', time=1987200.0)),
    #     (Network(net='SR'), Affiliation(net='SR', sta='ANMO', time=154051200.0)),
    # ]
    endtime = UTCDateTime('1980-01-01')
    q = req.query_network(session, Network, affiliation=Affiliation, endtime=endtime)
    out = q.order_by(Affiliation.time).all()
    assert (
        len(out) == 3 and
        out[0] == (d['IM'], d['IM_NV33']) and
        out[1] == (d['IM'], d['IM_NV32']) and
        out[2] == (d['SR'], d['SR_ANMO_0'])
    )

    # without Affiliation provided, time queries should fail
    with pytest.raises(NameError):
        out = req.query_network(session, Network, endtime=endtime).all()

    # if a query object is provided
    # should append Networks, Affiliations that contain the sta to the result set
    q = session.query(Site).filter(Site.sta.in_(['NV32', 'NV33']))
    q = req.query_network(session, Network, affiliation=Affiliation, with_query=q)
    out = q.order_by(Affiliation.time).all()
    # expected = [
    #     (Site(sta='NV33', ondate=1970024), Affiliation(net='IM', sta='NV33', time=-9999999999.999), Network(net='IM')),
    #     (Site(sta='NV32', ondate=1970024), Affiliation(net='IM', sta='NV32', time=1987200.0), Network(net='IM')),
    #     ]
    assert (
        len(out) == 2 and
        out[0] == (d['NV33'], d['IM_NV33'], d['IM']) and
        out[1] == (d['NV32'], d['IM_NV32'], d['IM'])
    )