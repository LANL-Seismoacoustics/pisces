"""
Useful Pytest fixtures for Pisces tests.

"""
from obspy import UTCDateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from pisces.tables.kbcore import *

engine = create_engine('sqlite:///:memory:', echo=False)
Session = sessionmaker(bind=engine)

def jdate(indate: str) -> int:
    # '2002-11-09' -> 2002323
    return int(UTCDateTime(indate).strftime('%Y%j'))

def jdate2epoch(jdate: int) -> float:
    # 2002323 -> 1037668325.0
    return UTCDateTime.strptime(str(jdate), '%Y%j').timestamp

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
    