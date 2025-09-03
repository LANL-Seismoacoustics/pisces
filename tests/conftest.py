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


# TODO: these are fixtures from test_fdsn that should be refactored here to avoid redundancy
@pytest.fixture(scope='session')
def engine():
    return create_engine('sqlite://')


@pytest.fixture(scope='session')
def tables(engine):
    Site.metadata.create_all(engine) # use the MetaData from any table
    yield
    Site.metadata.drop_all(engine)


# the "dbsession" test fixture allows your test function to get a clean session
# to an in-memory sqlite database.  You can add test data to it inside your test
# function, and the database will be clean for other tests when the test exits.
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


# test cases should include:
# - an array within one network (IM NVAR)
# - a station with multiple site entries in one network (IU ANMO)
# - a station with multiple network affiliations (IU|SR ANMO)
pytest.fixture(scope='module')
def testdata(session):
    data = {}
    ## 1. site Table
    data['site'] = dict(
        ANMO=Site(sta='ANMO', ondate=20100101, offdate=20301231, lat=34.9459, lon=-106.4572, elev=1.850, staname='ALBUQUERQUE, NEW MEXICO', statype='ss', refsta='ANMO', dnorth=0.0, deast=0.0),
        TPNV=Site(sta='TPNV', ondate=20100101, offdate=20301231, lat=36.9488, lon=-116.2495, elev=1.600, staname='TOPOPAH SPRINGS, NEVADA', statype='ss', refsta='TPNV', dnorth=0.0, deast=0.0),
        RSSD=Site(sta='RSSD', ondate=20100101, offdate=20301231, lat=44.1212, lon=-104.0359, elev=2.060, staname='BLACK HILLS, SOUTH DAKOTA', statype='ar', refsta='RSSD', dnorth=0.0, deast=0.0),
        KDAC=Site(sta='KDAK', ondate=20100101, offdate=20301231, lat=57.7828, lon=-152.5835, elev=0.152, staname='KODIAK ISLAND, ALASKA', statype='ss', refsta='KDAK', dnorth=0.0, deast=0.0),
        COLA=Site(sta='COLA', ondate=20100101, offdate=20301231, lat=64.8736, lon=-147.8616, elev=0.200, staname='COLLEGE OUTPOST, ALASKA', statype='ar', refsta='COLA', dnorth=0.0, deast=0.0),
    )
    ## 2. sitechan Table
    data['sitechan'] = dict(
        ANMO_Z=Sitechan(sta='ANMO', chan='BHZ', ondate=20100101, chanid=1, offdate=20301231, ctype='n', edepth=0.0, hang=0.0, vang=0.0, descrip='BROADBAND HIGH GAIN SEISMOMETER, VERTICAL'),
        ANMO_N=Sitechan(sta='ANMO', chan='BHN', ondate=20100101, chanid=2, offdate=20301231, ctype='n', edepth=0.0, hang=0.0, vang=90.0, descrip='BROADBAND HIGH GAIN SEISMOMETER, NORTH-SOUTH'),
        ANMO_E=Sitechan(sta='ANMO', chan='BHE', ondate=20100101, chanid=3, offdate=20301231, ctype='n', edepth=0.0, hang=90.0, vang=90.0, descrip='BROADBAND HIGH GAIN SEISMOMETER, EAST-WEST'),
        TPNV=Sitechan(sta='TPNV', chan='BHZ', ondate=20100101, chanid=4, offdate=20301231, ctype='n', edepth=0.0, hang=0.0, vang=0.0, descrip='BROADBAND HIGH GAIN SEISMOMETER, VERTICAL'),
        RSSD=Sitechan(sta='RSSD', chan='BHZ', ondate=20100101, chanid=5, offdate=20301231, ctype='n', edepth=0.0, hang=0.0, vang=0.0, descrip='BROADBAND HIGH GAIN SEISMOMETER, VERTICAL'),
        KDAK=Sitechan(sta='KDAK', chan='BHZ', ondate=20100101, chanid=6, offdate=20301231, ctype='n', edepth=0.0, hang=0.0, vang=0.0, descrip='BROADBAND HIGH GAIN SEISMOMETER, VERTICAL'),
        COLA=Sitechan(sta='COLA', chan='BHZ', ondate=20100101, chanid=7, offdate=20301231, ctype='n', edepth=0.0, hang=0.0, vang=0.0, descrip='BROADBAND HIGH GAIN SEISMOMETER, VERTICAL'),
    )
    ## 3. instrument Table
    data['instrument'] = dict(
        STS2=Instrument(inid=1, insname='STS-2', instype='BB', band='b', digital='d', samprate=40.0, ncalib=1.0, ncalper=1.0, dir='/data/responses/', dfile='STS2.resp', rsptype='paz'),
        CMG3T=Instrument(inid=2, insname='CMG-3T', instype='BB', band='b', digital='d', samprate=40.0, ncalib=1.0, ncalper=1.0, dir='/data/responses/', dfile='CMG3T.resp', rsptype='paz'),
        KS54000=Instrument(inid=3, insname='KS-54000', instype='BB', band='b', digital='d', samprate=20.0, ncalib=1.0, ncalper=1.0, dir='/data/responses/', dfile='KS54000.resp', rsptype='paz'),
    )
    ## 4. sensor Table
    data['sensor'] = dict(
        ANMO_Z=Sensor(sta='ANMO', chan='BHZ', time=1262304000.00000, endtime=1893456000.00000, inid=1, chanid=1, jdate=2010001, calratio=1.0, calper=1.0, tshift=0.0, instant='y'),
        ANMO_N=Sensor(sta='ANMO', chan='BHN', time=1262304000.00000, endtime=1893456000.00000, inid=1, chanid=2, jdate=2010001, calratio=1.0, calper=1.0, tshift=0.0, instant='y'),
        ANMO_E=Sensor(sta='ANMO', chan='BHE', time=1262304000.00000, endtime=1893456000.00000, inid=1, chanid=3, jdate=2010001, calratio=1.0, calper=1.0, tshift=0.0, instant='y'),
        TPNV=Sensor(sta='TPNV', chan='BHZ', time=1262304000.00000, endtime=1893456000.00000, inid=2, chanid=4, jdate=2010001, calratio=1.0, calper=1.0, tshift=0.0, instant='y'),
        RSSD=Sensor(sta='RSSD', chan='BHZ', time=1262304000.00000, endtime=1893456000.00000, inid=3, chanid=5, jdate=2010001, calratio=1.0, calper=1.0, tshift=0.0, instant='y'),
        KDAK=Sensor(sta='KDAK', chan='BHZ', time=1262304000.00000, endtime=1893456000.00000, inid=1, chanid=6, jdate=2010001, calratio=1.0, calper=1.0, tshift=0.0, instant='y'),
        COLA=Sensor(sta='COLA', chan='BHZ', time=1262304000.00000, endtime=1893456000.00000, inid=2, chanid=7, jdate=2010001, calratio=1.0, calper=1.0, tshift=0.0, instant='y'),
    )
    ## 5. network Table
    data['network'] = dict(
        GSN=Network(net='GSN', netname='GLOBAL SEISMIC NETWORK', nettype='ww', auth='IRIS', commid=1),
        ANSS=Network(net='ANSS', netname='ADVANCED NATIONAL SEISMIC SYSTEM', nettype='ww', auth='USGS', commid=2),
        IMS=Network(net='IMS', netname='INTERNATIONAL MONITORING SYSTEM', nettype='ww', auth='CTBTO', commid=3),
        AFTAC=Network(net='AFTAC', netname='AIR FORCE TECHNICAL APPLICATIONS CENTER', nettype='ww', auth='AFTAC', commid=4),
    )
    ## 6. affiliation Table
    data['affiliation'] = dict(
        GSN_ANMO=Affiliation(net='GSN', sta='ANMO', time=1262304000.00000, endtime=1893456000.00000),
        GSN_RSSD=Affiliation(net='GSN', sta='RSSD', time=1262304000.00000, endtime=1893456000.00000),
        ANSS_TPNV=Affiliation(net='ANSS', sta='TPNV', time=1262304000.00000, endtime=1893456000.00000),
        ISM_KDAK=Affiliation(net='IMS', sta='KDAK', time=1262304000.00000, endtime=1893456000.00000),
        AFTAC_COLA=Affiliation(net='AFTAC', sta='COLA', time=1262304000.00000, endtime=1893456000.00000),
    )
    ## 7. event Table
    data['event'] = dict(
        evid1001=Event(evid=1001, evname='NEVADA TEST 1', prefor=1, auth='USGS', commid=5),
        evid1002=Event(evid=1002, evname='NEW MEXICO EARTHQUAKE', prefor=2, auth='USGS', commid=6),
        evid1003=Event(evid=1003, evname='ALASKA EARTHQUAKE', prefor=3, auth='AEC', commid=7),
        evid1004=Event(evid=1004, evname='HAWAII VOLCANIC EVENT', prefor=4, auth='HVO', commid=8),
        evid1005=Event(evid=1005, evname='CALIFORNIA EARTHQUAKE', prefor=5, auth='USGS', commid=9),
    )
    ## 8. origin Table
    # INSERT INTO origin (lat, lon, depth, time, orid, evid, jdate, nass, ndef, ndp, grn, srn, etype, depdp, dtype, mb, mbid, ms, msid, ml, mlid, algorithm, auth, commid, lddate) VALUES
    data['origin'] = dict(
        orid1=Origin(lat=37.1166, lon=-116.0463, depth=0.5, time=1609459200.00000, orid=1, evid=1001, jdate=2021001, nass=8, ndef=15, ndp=5, grn=123, srn=45, etype='ex', depdp=0.5, dtype='F', mb=5.2, mbid=1, ms=5.5, msid=2, ml=5.3, mlid=3, algorightm='locsat', auth='USGS', commid=10),
        orid2=Origin(lat=34.9459, lon=-106.4572, depth=10.2, time=1609545600.00000, orid=2, evid=1002, jdate=2021002, nass=6, ndef=12, ndp=4, grn=124, srn=46, etype='qt', depdp=10.2, dtype='F', mb=4.8, mbid=4, ms=5.0, msid=5, ml=4.9, mlid=6, algorightm='locsat', auth='USGS', commid=11),
        orid3=Origin(lat=61.4478, lon=-149.7328, depth=15.3, time=1609632000.00000, orid=3, evid=1003, jdate=2021003, nass=7, ndef=14, ndp=6, grn=125, srn=47, etype='qt', depdp=15.3, dtype='F', mb=6.1, mbid=7, ms=6.3, msid=8, ml=6.2, mlid=9, algorightm='locsat', auth='AEC', commid=12),
        orid4=Origin(lat=19.4075, lon=-155.2833, depth=3.1, time=1609718400.00000, orid=4, evid=1004, jdate=2021004, nass=5, ndef=10, ndp=3, grn=126, srn=48, etype='qp', depdp=3.1, dtype='F', mb=4.2, mbid=10, ms=4.5, msid=11, ml=4.3, mlid=12, algorightm='locsat', auth='HVO', commid=13),
        orid5=Origin(lat=37.7749, lon=-122.4194, depth=8.7, time=1609804800.00000, orid=5, evid=1005, jdate=2021005, nass=9, ndef=18, ndp=7, grn=127, srn=49, etype='qt', depdp=8.7, dtype='F', mb=5.8, mbid=13, ms=6.0, msid=14, ml=5.9, mlid=15, algorightm='locsat', auth='USGS', commid=14),
    )
    ## 9. origerr Table
    data['origerr'] = dict(
        orid1=Origerr(orid=1, sxx=0.2500, syy=0.2500, szz=0.5000, stt=0.1000, sxy=0.0500, sxz=0.0500, syz=0.0500, stx=0.0500, sty=0.0500, stz=0.0500, sdobs=0.2000, smajax=0.3000, sminax=0.2000, strike=45.00, sdepth=0.5000, stime=0.100, conf=0.900, commid=15),
        orid2=Origerr(orid=2, sxx=0.3000, syy=0.3000, szz=0.6000, stt=0.1200, sxy=0.0600, sxz=0.0600, syz=0.0600, stx=0.0600, sty=0.0600, stz=0.0600, sdobs=0.2500, smajax=0.3500, sminax=0.2500, strike=50.00, sdepth=0.6000, stime=0.120, conf=0.850, commid=16),
        orid3=Origerr(orid=3, sxx=0.2000, syy=0.2000, szz=0.4000, stt=0.0800, sxy=0.0400, sxz=0.0400, syz=0.0400, stx=0.0400, sty=0.0400, stz=0.0400, sdobs=0.1500, smajax=0.2500, sminax=0.1500, strike=40.00, sdepth=0.4000, stime=0.080, conf=0.950, commid=17),
        orid4=Origerr(orid=4, sxx=0.3500, syy=0.3500, szz=0.7000, stt=0.1400, sxy=0.0700, sxz=0.0700, syz=0.0700, stx=0.0700, sty=0.0700, stz=0.0700, sdobs=0.3000, smajax=0.4000, sminax=0.3000, strike=55.00, sdepth=0.7000, stime=0.140, conf=0.800, commid=18),
        orid5=Origerr(orid=5, sxx=0.1500, syy=0.1500, szz=0.3000, stt=0.0600, sxy=0.0300, sxz=0.0300, syz=0.0300, stx=0.0300, sty=0.0300, stz=0.0300, sdobs=0.1000, smajax=0.2000, sminax=0.1000, strike=35.00, sdepth=0.3000, stime=0.060, conf=0.980, commid=19),
    )
    ## 10. arrival Table
    data['arrival'] = dict(
        ANMO1=Arrival(sta='ANMO', time=1609459230.00000, arid=1, jdate=2021001, stassid=1, chanid=1, chan='BHZ', iphase='P', stype='r', deltim=0.050, azimuth=120.50, delaz=2.00, slow=10.20, delslo=0.50, ema=0.80, rect=0.900, amp=1500.00, per=0.50, logat=1.50, clip='n', fm='c.', snr=15.00, qual='i', auth='auto', commid=20),
        ANMO2=Arrival(sta='ANMO', time=1609459260.00000, arid=2, jdate=2021001, stassid=1, chanid=2, chan='BHN', iphase='S', stype='r', deltim=0.080, azimuth=122.00, delaz=2.50, slow=5.50,  delslo=0.60, ema=0.75, rect=0.850, amp=2500.00, per=1.00, logat=2.00, clip='n', fm='c.', snr=12.00, qual='i', auth='auto', commid=21),
        TPNV=Arrival(sta='TPNV', time=1609459240.00000, arid=3, jdate=2021001, stassid=2, chanid=4, chan='BHZ', iphase='P', stype='r', deltim=0.060, azimuth=85.30,  delaz=1.80, slow=9.80,  delslo=0.40, ema=0.82, rect=0.920, amp=1400.00, per=0.48, logat=1.45, clip='n', fm='c.', snr=16.00, qual='i', auth='auto', commid=22),
        RSSD=Arrival(sta='RSSD', time=1609459250.00000, arid=4, jdate=2021001, stassid=3, chanid=5, chan='BHZ', iphase='P', stype='r', deltim=0.070, azimuth=65.20,  delaz=1.90, slow=9.50,  delslo=0.45, ema=0.81, rect=0.910, amp=1450.00, per=0.49, logat=1.48, clip='n', fm='c.', snr=14.50, qual='i', auth='auto', commid=23),
        KDAK=Arrival(sta='KDAK', time=1609632030.00000, arid=5, jdate=2021003, stassid=4, chanid=6, chan='BHZ', iphase='P', stype='r', deltim=0.040, azimuth=210.70, delaz=1.70, slow=10.50, delslo=0.55, ema=0.83, rect=0.930, amp=2200.00, per=0.52, logat=1.60, clip='n', fm='c.', snr=17.00, qual='i', auth='auto', commid=24),
        COLA=Arrival(sta='COLA', time=1609632020.00000, arid=6, jdate=2021003, stassid=5, chanid=7, chan='BHZ', iphase='P', stype='r', deltim=0.030, azimuth=195.30, delaz=1.60, slow=10.80, delslo=0.58, ema=0.84, rect=0.940, amp=2300.00, per=0.53, logat=1.65, clip='n', fm='c.', snr=18.00, qual='i', auth='auto', commid=25),
    )
    ## 11. assoc Table
    data['assoc'] = dict(
        arid1=Assoc(arid=1, orid=1, sta='ANMO', phase='P', belief=0.95, delta=2.50, seaz=120.50, esaz=300.50, timeres=0.020, timedef='d', azres=1.50, azdef='d', slores=0.50, slodef='d', emares=0.10, wgt=1.000, vmodel='iasp91', commid=26),
        arid2=Assoc(arid=2, orid=1, sta='ANMO', phase='S', belief=0.90, delta=2.50, seaz=122.00, esaz=302.00, timeres=0.050, timedef='d', azres=2.00, azdef='d', slores=0.80, slodef='d', emares=0.15, wgt=0.800, vmodel='iasp91', commid=27),
        arid3=Assoc(arid=3, orid=1, sta='TPNV', phase='P', belief=0.92, delta=1.80, seaz=85.30, esaz=265.30,  timeres=0.030, timedef='d', azres=1.60, azdef='d', slores=0.60, slodef='d', emares=0.12, wgt=0.900, vmodel='iasp91', commid=28),
        arid4=Assoc(arid=4, orid=1, sta='RSSD', phase='P', belief=0.93, delta=3.20, seaz=65.20, esaz=245.20,  timeres=0.040, timedef='d', azres=1.70, azdef='d', slores=0.55, slodef='d', emares=0.11, wgt=0.850, vmodel='iasp91', commid=29),
        arid5=Assoc(arid=5, orid=3, sta='KDAK', phase='P', belief=0.96, delta=1.20, seaz=210.70, esaz=30.70,  timeres=0.010, timedef='d', azres=1.40, azdef='d', slores=0.45, slodef='d', emares=0.08, wgt=1.000, vmodel='iasp91', commid=30),
        arid6=Assoc(arid=6, orid=3, sta='COLA', phase='P', belief=0.97, delta=0.80, seaz=195.30, esaz=15.30,  timeres=0.010, timedef='d', azres=1.30, azdef='d', slores=0.40, slodef='d', emares=0.07, wgt=1.000, vmodel='iasp91', commid=31),
    )
    ## 12. netmag Table
    data['netmag'] = dict(
        magid1=Netmag(magid=1, net='GSN', orid=1, evid=1001, magtype='mb', nsta=15, magnitude=5.20, uncertainty=0.10, auth='USGS', commid=32),
        magid2=Netmag(magid=2, net='GSN', orid=1, evid=1001, magtype='MS', nsta=12, magnitude=5.50, uncertainty=0.15, auth='USGS', commid=33),
        magid3=Netmag(magid=3, net='GSN', orid=1, evid=1001, magtype='ML', nsta=18, magnitude=5.30, uncertainty=0.12, auth='USGS', commid=34),
        magid4=Netmag(magid=4, net='ANSS', orid=2, evid=1002, magtype='mb', nsta=10, magnitude=4.80, uncertainty=0.08, auth='USGS', commid=35),
        magid5=Netmag(magid=5, net='ANSS', orid=2, evid=1002, magtype='MS', nsta=8, magnitude=5.00, uncertainty=0.12, auth='USGS', commid=36),
        magid6=Netmag(magid=6, net='ANSS', orid=2, evid=1002, magtype='ML', nsta=14, magnitude=4.90, uncertainty=0.10, auth='USGS', commid=37),
        magid7=Netmag(magid=7, net='AFTAC', orid=3, evid=1003, magtype='mb', nsta=16, magnitude=6.10, uncertainty=0.09, auth='AEC', commid=38),
        magid8=Netmag(magid=8, net='AFTAC', orid=3, evid=1003, magtype='MS', nsta=12, magnitude=6.30, uncertainty=0.14, auth='AEC', commid=39),
        magid9=Netmag(magid=9, net='AFTAC', orid=3, evid=1003, magtype='ML', nsta=20, magnitude=6.20, uncertainty=0.11, auth='AEC', commid=40),
    )
    ## 13. stamag Table
    data['stamag'] = dict(
        ampid1=Stamag(magid=1, ampid=1, sta='ANMO', arid=1, orid=1, evid=1001, phase='P', delta=2.50, magtype='mb', magnitude=5.30, uncertainty=0.15, magres=0.10, magdef='d', mmodel='veith', auth='USGS', commid=41),
        ampid2=Stamag(magid=1, ampid=2, sta='TPNV', arid=3, orid=1, evid=1001, phase='P', delta=1.80, magtype='mb', magnitude=5.10, uncertainty=0.12, magres=-0.10, magdef='d', mmodel='veith', auth='USGS', commid=42),
        ampid3=Stamag(magid=2, ampid=3, sta='ANMO', arid=2, orid=1, evid=1001, phase='S', delta=2.50, magtype='MS', magnitude=5.60, uncertainty=0.18, magres=0.10, magdef='d', mmodel='Prague', auth='USGS', commid=43),
        ampid4=Stamag(magid=2, ampid=4, sta='TPNV', arid=3, orid=1, evid=1001, phase='P', delta=1.80, magtype='MS', magnitude=5.40, uncertainty=0.16, magres=-0.10, magdef='d', mmodel='Prague', auth='USGS', commid=44),
        ampid5=Stamag(magid=7, ampid=5, sta='KDAK', arid=5, orid=3, evid=1003, phase='P', delta=1.20, magtype='mb', magnitude=6.20, uncertainty=0.14, magres=0.10, magdef='d', mmodel='veith', auth='AEC', commid=45),
        ampid6=Stamag(magid=7, ampid=6, sta='COLA', arid=6, orid=3, evid=1003, phase='P', delta=0.80, magtype='mb', magnitude=6.00, uncertainty=0.11, magres=-0.10, magdef='d', mmodel='veith', auth='AEC', commid=46),
    )
    ## 14. wfdisc Table
    data['wfdisc'] = dict(
        wfid1=Wfdisc(sta='ANMO', chan='BHZ', time=1609459200.00000, wfid=1, chanid=1, jdate=2021001, endtime=1609459500.00000, nsamp=12000, samprate=40.0000000, calib=1.000000, calper=1.000000, instype='STS-2', segtype='o', datatype='s4', clip='n', dir='/data/ANMO/2021/', dfile='ANMO_BHZ_20210101.w', foff=0, commid=47),
        wfid2=Wfdisc(sta='ANMO', chan='BHN', time=1609459200.00000, wfid=2, chanid=2, jdate=2021001, endtime=1609459500.00000, nsamp=12000, samprate=40.0000000, calib=1.000000, calper=1.000000, instype='STS-2', segtype='o', datatype='s4', clip='n', dir='/data/ANMO/2021/', dfile='ANMO_BHN_20210101.w', foff=0, commid=48),
        wfid3=Wfdisc(sta='ANMO', chan='BHE', time=1609459200.00000, wfid=3, chanid=3, jdate=2021001, endtime=1609459500.00000, nsamp=12000, samprate=40.0000000, calib=1.000000, calper=1.000000, instype='STS-2', segtype='o', datatype='s4', clip='n', dir='/data/ANMO/2021/', dfile='ANMO_BHE_20210101.w', foff=0, commid=49),
        wfid4=Wfdisc(sta='TPNV', chan='BHZ', time=1609459200.00000, wfid=4, chanid=4, jdate=2021001, endtime=1609459500.00000, nsamp=12000, samprate=40.0000000, calib=1.000000, calper=1.000000, instype='CMG-3T', segtype='o', datatype='s4', clip='n', dir='/data/TPNV/2021/', dfile='TPNV_BHZ_20210101.w', foff=0, commid=50),
        wfid5=Wfdisc(sta='RSSD', chan='BHZ', time=1609459200.00000, wfid=5, chanid=5, jdate=2021001, endtime=1609459500.00000, nsamp=12000, samprate=40.0000000, calib=1.000000, calper=1.000000, instype='KS-54000', segtype='o', datatype='s4', clip='n', dir='/data/RSSD/2021/', dfile='RSSD_BHZ_20210101.w', foff=0, commid=51),
        wfid6=Wfdisc(sta='KDAK', chan='BHZ', time=1609632000.00000, wfid=6, chanid=6, jdate=2021003, endtime=1609632300.00000, nsamp=12000, samprate=40.0000000, calib=1.000000, calper=1.000000, instype='STS-2', segtype='o', datatype='s4', clip='n', dir='/data/KDAK/2021/', dfile='KDAK_BHZ_20210103.w', foff=0, commid=52),
        wfid7=Wfdisc(sta='COLA', chan='BHZ', time=1609632000.00000, wfid=7, chanid=7, jdate=2021003, endtime=1609632300.00000, nsamp=12000, samprate=40.0000000, calib=1.000000, calper=1.000000, instype='CMG-3T', segtype='o', datatype='s4', clip='n', dir='/data/COLA/2021/', dfile='COLA_BHZ_20210103.w', foff=0, commid=53),
    )
    ## 15. wftag Table

    for table in data:
        session.add_all(data[table].values())
        session.commit()

    yield session, data

    for table in data:
        for row in data[table].values():
            session.delete(row)
        session.commit()
