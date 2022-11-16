# coding: utf-8
"""
Antelope v4.11 Datascope database schema


"""
from datetime import datetime
from sqlalchemy import Date, DateTime, Float, Numeric, String, Integer
from sqlalchemy import Column, Table, func
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declared_attr

from obspy.core import UTCDateTime
from pisces.schema.util import PiscesMeta
from pisces.schema.util import parse_int, parse_float, parse_str

from pisces.io.trace import wfdisc2trace

Base = declarative_base(metaclass=PiscesMeta, constructor=None)

# COLUMN DEFINITIONS
# Generic SQLA types, compatible with different backends
# !! info dictionary defines the external representations (NumPy, text files)
#   and default values for the mapped class representation.
# XXX: for numeric types, maximum width is not enforced!
# NOTE: info['dtype'] for floats/ints should match the system default for Python
#       "{:f}".format(numpyfloat/int) to work, b/c it can use the builtin float
#       __format__().  use 'float' or 'int'
#       See:
#       http://stackoverflow.com/questions/16928644/floats-in-numpy-structured-array-and-native-string-formatting-with-format

def strip(s):
    return str(s).strip()

DATEFMT = '%y-%m-%d %H:%M:%S'
def dtfn(s):
    try:
        dt = datetime.strptime(s.strip(), DATEFMT)
    except ValueError:
        # Antelope convention
        dt = UTCDateTime(float(s)).datetime
    return dt


algorithm = Column(String(15),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a15', 'width': 15, 'format': '15.15s'})
amp = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 10, 'format': '10.1f'})
ampid = Column(Integer, nullable=False,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
amptime = Column(Float(53), info={'default': -9999999999.999,
        'parse': parse_float, 'dtype': 'float', 'width': 17, 'format': '17.5f'})
amptype = Column(String(8),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a8', 'width': 8, 'format': '8.8s'})
arid = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
auth = Column(String(15),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a15', 'width': 15, 'format': '15s'})
azdef = Column(String(1),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
azimuth = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
azres = Column(Float(24),
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.1f'})
band = Column(String(1),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
belief = Column(Float(24),
        info={'default': -9.99, 'parse': parse_float, 'dtype': 'float', 'width': 4, 'format': '4.2f'})
calib = Column(Float(24),
        info={'default': 0.0, 'parse': parse_float, 'dtype': 'float', 'width': 16, 'format': '16.9f'})
calper = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 16, 'format': '16.6f'})
calratio = Column(Float(24),
        info={'default': 1.0, 'parse': parse_float, 'dtype': 'float', 'width': 16, 'format': '16.6f'})
chan = Column(String(8),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a8', 'width': 8, 'format': '8.8s'})
chanid = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
clip = Column(String(1),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
commid = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
conf = Column(Float(24),
        info={'default': 0, 'parse': parse_float, 'dtype': 'float', 'width': 5, 'format': '5.3f'})
ctype = Column(String(4),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a4', 'width': 4, 'format': '4.4s'})
datatype = Column(String(2),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a2', 'width': 2, 'format': '2.2s'})
deast = Column(Float(24),
        info={'default': 0.0, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})
delaz = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
delslo = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
delta = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 8, 'format': '8.3f'})
deltaf = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.3f'})
deltim = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 6, 'format': '6.3f'})
depdp = Column(Float(24),
        info={'default': -999, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})
depth = Column(Float(24),
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})
descrip = Column(String(50),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a50', 'width': 50, 'format': '50.50s'})
dfile = Column(String(32),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a32', 'width': 32, 'format': '32.32s'})
digital = Column(String(1),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
dir = Column(String(64),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a64', 'width': 64, 'format': '64.64s'})
dnorth = Column(Float(24),
        info={'default': 0.0, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})
dtype = Column(String(1),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
duration = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
edepth = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})
elev = Column(Float(24),
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})
ema = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
emares = Column(Float(24),
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.1f'})
endtime = Column(Float(53), info={'default':  9999999999.999,
        'parse': parse_float, 'dtype': 'float', 'width': 17, 'format': '17.5f'})
esaz = Column(Float(24),
        info={'default': -1, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
etype = Column(String(2),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a2', 'width': 2, 'format': '2.2s'})
evid = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
evname = Column(String(15),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a15', 'width': 15, 'format': '15.15s'})
fm = Column(String(2),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a2', 'width': 2, 'format': '2.2s'})
foff = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 10, 'format': '10d'})
grn = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
grname = Column(String(40),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a40', 'width': 40, 'format': '40.40s'})
hang = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 6, 'format': '6.1f'})
inarrival = Column(String(1),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
inid = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
insname = Column(String(50),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a50', 'width': 50, 'format': '50.50s'})
instant = Column(String(1),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
instype = Column(String(6),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a6', 'width': 6, 'format': '6.6s'})
iphase = Column(String(8),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a8', 'width': 8, 'format': '8.8s'})
jdate = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
keyname = Column(String(15),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a15', 'width': 15, 'format': '15.15s'})
keyvalue = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
lat = Column(Float(53),
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})
lddate = Column(DateTime, nullable=False, onupdate=datetime.now,
        info={'default': datetime.now, 'parse': dtfn, 'dtype': 'O', 'width': 17, 'format': DATEFMT})
lineno = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
logat = Column(Float(24),
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
lon = Column(Float(53),
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})
magid = Column(Integer, nullable=False,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
magnitude = Column(Float(24),
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
magres = Column(Float(24),
        info={'default': -999, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
magdef = Column(String(1),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
magtype = Column(String(6),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a6', 'width': 6, 'format': '6.6s'})
mb = Column(Float(24),
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
mbid = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
ml = Column(Float(24),
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
mlid = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
ms = Column(Float(24),
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
msid = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
mmodel = Column(String(15),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a15', 'width': 15, 'format': '15.15s'})
nass = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 4, 'format': '4d'})
ncalib = Column(Float(24),
        info={'default': 1.0, 'parse': parse_float, 'dtype': 'float', 'width': 16, 'format': '16.6f'})
ncalper = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 16, 'format': '16.6f'})
ndef = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 4, 'format': '4d'})
ndp = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 4, 'format': '4d'})
net = Column(String(8),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a8', 'width': 8, 'format': '8.8s'})
netname = Column(String(80),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a80', 'width': 80, 'format': '80.80s'})
nettype = Column(String(4),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a4', 'width': 4, 'format': '4.4s'})
nsamp = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
nsta = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
offdate = Column(Integer,
        info={'default': 2286324, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
ondate = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
orid = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
parid = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
per = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
phase = Column(String(8),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a8', 'width': 8, 'format': '8.8s'})
prefor = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
qual = Column(String(1),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
rect = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.3f'})
refsta = Column(String(6),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a6', 'width': 6, 'format': '6.6s'})
remark = Column(String(80),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a80', 'width': 80, 'format': '80.80s'})
review =  Column(String(4),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a4', 'width': 4, 'format': '4.4s'})
rsptype = Column(String(6),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a6', 'width': 6, 'format': '6.6s'})
samprate = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 11, 'format': '11.7f'})
sdepth = Column(Float(24),
        info={'default': -1, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})
sdobs = Column(Float(24),
        info={'default': -1, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})
seaz = Column(Float(24),
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
segtype = Column(String(1),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
slodef = Column(String(1),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
slores = Column(Float(24),
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
slow = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float','width': 7, 'format': '7.2f'})
smajax = Column(Float(24),
        info={'default': -1, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})
sminax = Column(Float(24),
        info={'default': -1, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})
snr = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 10, 'format': '10.5f'})
srn = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
srname = Column(String(40),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a40', 'width': 40, 'format': '40.40s'})
sta = Column(String(6),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a6', 'width': 6, 'format': '6.6s'})
staname = Column(String(50),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a50', 'width': 50, 'format': '50.50s'})
stassid = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
statype = Column(String(4),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a4', 'width': 4, 'format': '4.4s'})
stime = Column(Float(24),
        info={'default': -1, 'parse': parse_float, 'dtype': 'float', 'width': 8, 'format': '8.2f'})
strike = Column(Float(24),
        info={'default': -1, 'parse': parse_float, 'dtype': 'float', 'width': 6, 'format': '6.2f'})
stt = Column(Float(24),
        info={'default': -100000000, 'parse': parse_float, 'dtype': 'float', 'width': 15, 'format': '15.4f'})
stx = Column(Float(24),
        info={'default': -100000000, 'parse': parse_float, 'dtype': 'float', 'width': 15, 'format': '15.4f'})
sty = Column(Float(24),
        info={'default': -100000000, 'parse': parse_float, 'dtype': 'float', 'width': 15, 'format': '15.4f'})
stype = Column(String(1),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
stz = Column(Float(24),
        info={'default': -100000000, 'parse': parse_float, 'dtype': 'float', 'width': 15, 'format': '15.4f'})
sxx = Column(Float(24),
        info={'default': -100000000, 'parse': parse_float, 'dtype': 'float', 'width': 15, 'format': '15.4f'})
sxy = Column(Float(24),
        info={'default': -100000000, 'parse': parse_float, 'dtype': 'float', 'width': 15, 'format': '15.4f'})
sxz = Column(Float(24),
        info={'default': -100000000, 'parse': parse_float, 'dtype': 'float', 'width': 15, 'format': '15.4f'})
syy = Column(Float(24),
        info={'default': -100000000, 'parse': parse_float, 'dtype': 'float', 'width': 15, 'format': '15.4f'})
syz = Column(Float(24),
        info={'default': -100000000, 'parse': parse_float, 'dtype': 'float', 'width': 15, 'format': '15.4f'})
szz = Column(Float(24),
        info={'default': -100000000, 'parse': parse_float, 'dtype': 'float', 'width': 15, 'format': '15.4f'})
tagid = Column(Integer,
        info={'default': -1, 'parse': parse_float, 'dtype': 'float', 'width': 8, 'format': '8d'})
tagname = Column(String(8),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a8', 'width': 8, 'format': '8.8s'})
time = Column(Float(53),
        info={'default': -9999999999.999, 'parse': parse_float, 'dtype': 'float', 'width': 17, 'format': '17.5f'})
timedef = Column(String(1),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
timeres = Column(Float(24),
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 8, 'format': '8.3f'})
tshift = Column(Float(24),
        info={'default': -100000000, 'parse': parse_float, 'dtype': 'float', 'width': 6, 'format': '6.2f'})
uncertainty = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
units = Column(String(12),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a12', 'width': 12, 'format': '12.12s'})
vang = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 6, 'format': '6.1f'})
vmodel = Column(String(15),
        info={'default': '-', 'parse': parse_str, 'dtype': 'a15', 'width': 15, 'format': '15.15s'})
wfid = Column(Integer,
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
wgt = Column(Float(24),
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 6, 'format': '6.3f'})

class Affiliation(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('net', 'sta', 'time'),)

    net = net.copy()
    sta = sta.copy()
    lddate = lddate.copy()


class Amplitude(Base):
    __abstract__ =True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('ampid'),)

    ampid = ampid._copy()
    arid = arid._copy()
    parid = parid._copy()
    chan = chan._copy()
    amp = amp._copy()
    per = per._copy()
    snr = snr._copy()
    amptime = amptime._copy()
    time = time._copy()
    duration = duration._copy()
    deltaf = deltaf._copy()
    amptype = amptype._copy()
    units = units._copy()
    clip = clip._copy()
    inarrival = inarrival._copy()
    auth = auth._copy()
    lddate = lddate._copy()


class Arrival(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('arid'),
                UniqueConstraint(u'sta', u'time', u'chan', u'iphase', u'auth'),)

    sta = sta._copy()
    time = time._copy()
    arid = arid._copy()
    jdate = jdate._copy()
    stassid = stassid._copy()
    chanid = chanid._copy()
    chan = chan._copy()
    iphase = iphase._copy()
    stype = stype._copy()
    deltim = deltim._copy()
    azimuth = azimuth._copy()
    delaz = delaz._copy()
    slow = slow._copy()
    delslo = delslo._copy()
    ema = ema._copy()
    rect = rect._copy()
    amp = amp._copy()
    per = per._copy()
    logat = logat._copy()
    clip = clip._copy()
    fm = fm._copy()
    snr = snr._copy()
    qual = qual._copy()
    auth = auth._copy()
    commid = commid._copy()
    lddate = lddate._copy()


class Assoc(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('arid','orid'),
                UniqueConstraint('arid'),)

    arid = arid._copy()
    orid = orid._copy()
    sta = sta._copy()
    phase = phase._copy()
    belief = belief._copy()
    delta = delta._copy()
    seaz = seaz._copy()
    esaz = esaz._copy()
    timeres = timeres._copy()
    timedef = timedef._copy()
    azres = azres._copy()
    azdef = azdef._copy()
    slores = slores._copy()
    slodef = slodef._copy()
    emares = emares._copy()
    wgt = wgt._copy()
    vmodel = vmodel._copy()
    commid = commid._copy()
    lddate = lddate._copy()


class Event(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('evid'),
                UniqueConstraint('prefor'),)

    evid = evid._copy()
    evname = evname._copy()
    prefor = prefor._copy()
    auth = auth._copy()
    commid = commid._copy()
    lddate = lddate._copy()


class Gregion(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('grn'),)

    grn = grn._copy()
    grname = grname._copy()
    lddate = lddate._copy()


class Instrument(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('inid'),)

    inid = inid._copy()
    insname = insname._copy()
    instype = instype._copy()
    band = band._copy()
    digital = digital._copy()
    samprate = samprate._copy()
    ncalib = ncalib._copy()
    ncalper = ncalper._copy()
    dir = dir._copy()
    dfile = dfile._copy()
    rsptype = rsptype._copy()
    lddate = lddate._copy()


class Lastid(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('keyname'),
                UniqueConstraint(u'keyname', u'keyvalue'),)

    keyname = keyname._copy()
    keyvalue = keyvalue._copy()
    lddate = lddate._copy()


class Netmag(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('magid'),
                UniqueConstraint('magid', 'orid'),)

    magid = magid._copy()
    net = net._copy()
    orid = orid._copy()
    evid = evid._copy()
    magtype = magtype._copy()
    nsta = nsta._copy()
    magnitude = magnitude._copy()
    uncertainty = uncertainty._copy()
    auth = auth._copy()
    commid = commid._copy()
    lddate = lddate._copy()


class Network(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('net'),)

    net = net.copy()
    netname = netname._copy()
    nettype = nettype._copy()
    auth = auth._copy()
    commid = commid._copy()
    lddate = lddate._copy()


class Origerr(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('orid'),)

    orid = orid._copy()
    sxx = sxx._copy()
    syy = syy._copy()
    szz = szz._copy()
    stt = stt._copy()
    sxy = sxy._copy()
    sxz = sxz._copy()
    syz = syz._copy()
    stx = stx._copy()
    sty = sty._copy()
    stz = stz._copy()
    sdobs = sdobs._copy()
    smajax = smajax._copy()
    sminax = sminax._copy()
    strike = strike._copy()
    sdepth = sdepth._copy()
    stime = stime._copy()
    conf = conf._copy()
    commid = commid._copy()
    lddate = lddate._copy()


class Origin(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (UniqueConstraint('lat','lon','depth','time','auth'),
                PrimaryKeyConstraint('orid'),)

    lat = lat._copy()
    lon = lon._copy()
    depth = depth._copy()
    time = time._copy()
    orid = orid._copy()
    evid = evid._copy()
    jdate = jdate._copy()
    nass = nass._copy()
    ndef = ndef._copy()
    ndp = ndp._copy()
    grn = grn._copy()
    srn = srn._copy()
    etype = etype._copy()
    review = review._copy()
    depdp = depdp._copy()
    dtype = dtype._copy()
    mb = mb._copy()
    mbid = mbid._copy()
    ms = ms._copy()
    msid = msid._copy()
    ml = ml._copy()
    mlid = mlid._copy()
    algorithm = algorithm._copy()
    auth = auth._copy()
    commid = commid._copy()
    lddate = lddate._copy()


class Remark(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('commid','lineno'),)

    commid = commid._copy()
    lineno = lineno._copy()
    remark = remark._copy()
    lddate = lddate._copy()


class Sensor(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('sta','chan','time','endtime'),)

    sta = sta._copy()
    chan = chan._copy()
    time = time._copy()
    endtime = endtime._copy()
    inid = inid._copy()
    chanid = chanid._copy()
    jdate = jdate._copy()
    calratio = calratio._copy()
    calper = calper._copy()
    tshift = tshift._copy()
    instant = instant._copy()
    lddate = lddate._copy()


class Site(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('sta','ondate'),)

    sta = sta._copy()
    ondate = ondate._copy()
    offdate = offdate._copy()
    lat = lat._copy()
    lon = lon._copy()
    elev = elev._copy()
    staname = staname._copy()
    statype = statype._copy()
    refsta = refsta._copy()
    dnorth = dnorth._copy()
    deast = deast._copy()
    lddate = lddate._copy()


class Sitechan(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (UniqueConstraint('sta','chan','ondate'),
                PrimaryKeyConstraint('sta','chan','ondate','offtime'),)

    sta = sta._copy()
    chan = chan._copy()
    ondate = ondate._copy()
    chanid = chanid._copy()
    offdate = offdate._copy()
    ctype = ctype._copy()
    edepth = edepth._copy()
    hang = hang._copy()
    vang = vang._copy()
    descrip = descrip._copy()
    lddate = lddate._copy()


class Sregion(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('srn'),)

    srn = srn.copy()
    srname = srname._copy()
    lddate = lddate.copy()


class Stamag(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('magid', 'sta', 'arid'),)

    magid = magid.copy()
    sta = sta.copy()
    arid = arid.copy()
    orid = orid.copy()
    evid = evid.copy()
    phase = phase.copy()
    magtype = magtype.copy()
    magnitude = magnitude.copy()
    uncertainty = uncertainty.copy()
    auth = auth.copy()
    commid = commid.copy()
    lddate = lddate._copy()


class Wfdisc(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (UniqueConstraint('wfid','dir','dfile'),
                PrimaryKeyConstraint('wfid'),)

    def to_trace(self):
         """
         Read the wfdisc line into a Trace instance.  Minimal header.

         Returns
         -------
         obspy.Trace

         """
         return wfdisc2trace(self)

    sta = sta._copy()
    chan = chan._copy()
    time = time._copy()
    wfid = wfid._copy()
    chanid = chanid._copy()
    jdate = jdate._copy()
    endtime = endtime._copy()
    nsamp = nsamp._copy()
    samprate = samprate._copy()
    calib = calib._copy()
    calper = calper._copy()
    instype = instype._copy()
    segtype = segtype._copy()
    datatype = datatype._copy()
    clip = clip._copy()
    dir = dir._copy()
    dfile = dfile._copy()
    foff = foff._copy()
    commid = commid._copy()
    lddate = lddate._copy()


class Wftag(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('tagid'),
                UniqueConstraint('tagname','tagid','wfid'),)

    tagname = tagname._copy()
    tagid = tagid._copy()
    wfid = wfid._copy()
    lddate = lddate._copy()


