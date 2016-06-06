# coding: utf-8
"""
Center for Seismic Studies relational database schema 3.0 (CSS3.0)


"""
from datetime import datetime
from sqlalchemy import Date, DateTime, Float, Numeric, String, Integer
from sqlalchemy import Column, Table, func
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
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
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 11, 'format': '11.2f'})
ampid = Column(Integer, nullable=False, 
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})
amptime = Column(Float(53), info={'default': -9999999999.999, 
        'parse': parse_float, 'dtype': 'float', 'width': 17, 'format': '17.5f'})
amptype = Column(String(8), 
        info={'default': '-', 'parse': parse_str, 'dtype': 'a8', 'width': 8, 'format': '8.8s'})
arid = Column(Integer, 
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})
auth = Column(String(20), 
        info={'default': '-', 'parse': parse_str, 'dtype': 'a20', 'width': 20, 'format': '20s'})
azdef = Column(String(1), 
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
azimuth = Column(Float(24), 
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
azres = Column(Float(24), 
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.1f'})
band = Column(String(1), 
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
belief = Column(Float(24), 
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 4, 'format': '4.2f'})
calib = Column(Float(24), 
        info={'default': 1.0, 'parse': parse_float, 'dtype': 'float', 'width': 16, 'format': '16.6f'})
calper = Column(Float(24), 
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 16, 'format': '16.6f'})
calratio = Column(Float(24), 
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 16, 'format': '16.6f'})
chan = Column(String(8), 
        info={'default': '-', 'parse': parse_str, 'dtype': 'a8', 'width': 8, 'format': '8.8s'})
chanid = Column(Integer, 
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
clip = Column(String(1), 
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
commid = Column(Integer, 
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
conf = Column(Float(24), 
        info={'default': -1, 'parse': parse_float, 'dtype': 'float', 'width': 5, 'format': '5.3f'})
ctype = Column(String(4), 
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
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
etype = Column(String(7), 
        info={'default': '-', 'parse': parse_str, 'dtype': 'a7', 'width': 7, 'format': '7.7s'})
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
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})
lat = Column(Float(53), 
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})
#lddate = Column(DateTime, nullable=False, onupdate=datetime.now,
#        info={'default': datetime.now, 'dtype': '|O8', 'width': 17, 'format': '%y-%m-%d %H:%M:%S'}) 
lddate = Column(DateTime, nullable=False, onupdate=datetime.now,
        info={'default': datetime.now, 'parse': dtfn, 'dtype': 'O', 'width': 17, 'format': DATEFMT})
#        info={'default': datetime.now, 'dtype': 'M', 'width': 17, 'format': '%y-%m-%d %H:%M:%S'}) 
lineno = Column(Integer, 
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
logat = Column(Float(24), 
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
lon = Column(Float(53), 
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})
magid = Column(Integer, nullable=False, 
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})
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
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})
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
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 10, 'format': '10.2f'})
srn = Column(Integer, 
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})
srname = Column(String(80), 
        info={'default': '-', 'parse': parse_str, 'dtype': 'a80', 'width': 80, 'format': '80.80s'})
sta = Column(String(6), 
        info={'default': '-', 'parse': parse_str, 'dtype': 'a6', 'width': 6, 'format': '6.6s'})
staname = Column(String(50), 
        info={'default': '-', 'parse': parse_str, 'dtype': 'a50', 'width': 50, 'format': '50.50s'})
stassid = Column(Integer, 
        info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})
statype = Column(String(4), 
        info={'default': '-', 'parse': parse_str, 'dtype': 'a4', 'width': 4, 'format': '4.4s'})
stime = Column(Float(24),
        info={'default': -1, 'parse': parse_float, 'dtype': 'float', 'width': 6, 'format': '6.2f'})
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
        info={'default': -1, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9d'})
tagname = Column(String(8), 
        info={'default': '-', 'parse': parse_str, 'dtype': 'a8', 'width': 8, 'format': '8.8s'})
time = Column(Float(53), 
        info={'default': -9999999999.999, 'parse': parse_float, 'dtype': 'float', 'width': 17, 'format': '17.5f'})
timedef = Column(String(1), 
        info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})
timeres = Column(Float(24), 
        info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 8, 'format': '8.3f'})
tshift = Column(Float(24), 
        info={'default': -100000000, 'parse': parse_float, 'dtype': 'float', 'width': 16, 'format': '16.2f'})
uncertainty = Column(Float(24), 
        info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})
units = Column(String(15), 
        info={'default': '-', 'parse': parse_str, 'dtype': 'a15', 'width': 15, 'format': '15.15s'})
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
    time = time.copy()
    endtime = endtime.copy()
    lddate = lddate.copy()


class Amplitude(Base):
    __abstract__ =True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('ampid'),)

    ampid = ampid.copy()
    arid = arid.copy()
    parid = parid.copy()
    chan = chan.copy()
    amp = amp.copy()
    per = per.copy()
    snr = snr.copy()
    amptime = amptime.copy()
    time = time.copy()
    duration = duration.copy()
    deltaf = deltaf.copy()
    amptype = amptype.copy()
    units = units.copy()
    clip = clip.copy()
    inarrival = inarrival.copy()
    auth = auth.copy()
    lddate = lddate.copy()


class Arrival(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('arid'),
                UniqueConstraint(u'sta', u'time', u'chan', u'iphase', u'auth'),)

    sta = sta.copy()
    time = time.copy()
    arid = arid.copy()
    jdate = jdate.copy()
    stassid = stassid.copy()
    chanid = chanid.copy()
    chan = chan.copy()
    iphase = iphase.copy()
    stype = stype.copy()
    deltim = deltim.copy()
    azimuth = azimuth.copy()
    delaz = delaz.copy()
    slow = slow.copy()
    delslo = delslo.copy()
    ema = ema.copy()
    rect = rect.copy()
    amp = amp.copy()
    per = per.copy()
    logat = logat.copy()
    clip = clip.copy()
    fm = fm.copy()
    snr = snr.copy()
    qual = qual.copy()
    auth = auth.copy()
    commid = commid.copy()
    lddate = lddate.copy()


class Assoc(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('arid','orid'),
                UniqueConstraint('arid'),)

    arid = arid.copy()
    orid = orid.copy()
    sta = sta.copy()
    phase = phase.copy()
    belief = belief.copy()
    delta = delta.copy()
    seaz = seaz.copy()
    esaz = esaz.copy()
    timeres = timeres.copy()
    timedef = timedef.copy()
    azres = azres.copy()
    azdef = azdef.copy()
    slores = slores.copy()
    slodef = slodef.copy()
    emares = emares.copy()
    wgt = wgt.copy()
    vmodel = vmodel.copy()
    commid = commid.copy()
    lddate = lddate.copy()


class Event(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('evid'), 
                UniqueConstraint('prefor'),)

    evid = evid.copy()
    evname = evname.copy()
    prefor = prefor.copy()
    auth = auth.copy()
    commid = commid.copy()
    lddate = lddate.copy()


class Gregion(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('grn'),)

    grn = grn.copy()
    grname = grname.copy()
    lddate = lddate.copy()


class Instrument(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('inid'),)

    inid = inid.copy()
    insname = insname.copy()
    instype = instype.copy()
    band = band.copy()
    digital = digital.copy()
    samprate = samprate.copy()
    ncalib = ncalib.copy()
    ncalper = ncalper.copy()
    dir = dir.copy()
    dfile = dfile.copy()
    rsptype = rsptype.copy()
    lddate = lddate.copy()


class Lastid(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls): 
        return (PrimaryKeyConstraint('keyname'),
                UniqueConstraint(u'keyname', u'keyvalue'),)

    keyname = keyname.copy()
    keyvalue = keyvalue.copy()
    lddate = lddate.copy()


class Netmag(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('magid'),
                UniqueConstraint('magid', 'orid'),)

    magid = magid.copy()
    net = net.copy()
    orid = orid.copy()
    evid = evid.copy()
    magtype = magtype.copy()
    nsta = nsta.copy()
    magnitude = magnitude.copy()
    uncertainty = uncertainty.copy()
    auth = auth.copy()
    commid = commid.copy()
    lddate = lddate.copy()


class Network(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('net'),)

    net = net.copy()
    netname = netname.copy()
    nettype = nettype.copy()
    auth = auth.copy()
    commid = commid.copy()
    lddate = lddate.copy()


class Origerr(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('orid'),)

    orid = orid.copy()
    sxx = sxx.copy()
    syy = syy.copy()
    szz = szz.copy()
    stt = stt.copy()
    sxy = sxy.copy()
    sxz = sxz.copy()
    syz = syz.copy()
    stx = stx.copy()
    sty = sty.copy()
    stz = stz.copy()
    sdobs = sdobs.copy()
    smajax = smajax.copy()
    sminax = sminax.copy()
    strike = strike.copy()
    sdepth = sdepth.copy()
    stime = stime.copy()
    conf = conf.copy()
    commid = commid.copy()
    lddate = lddate.copy()


class Origin(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (UniqueConstraint('lat','lon','depth','time','auth'),
                PrimaryKeyConstraint('orid'),)

    lat = lat.copy()
    lon = lon.copy()
    depth = depth.copy()
    time = time.copy()
    orid = orid.copy()
    evid = evid.copy()
    jdate = jdate.copy()
    nass = nass.copy()
    ndef = ndef.copy()
    ndp = ndp.copy()
    grn = grn.copy()
    srn = srn.copy()
    etype = etype.copy()
    depdp = depdp.copy()
    dtype = dtype.copy()
    mb = mb.copy()
    mbid = mbid.copy()
    ms = ms.copy()
    msid = msid.copy()
    ml = ml.copy()
    mlid = mlid.copy()
    algorithm = algorithm.copy()
    auth = auth.copy()
    commid = commid.copy()
    lddate = lddate.copy()


class Remark(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('commid','lineno'),)

    commid = commid.copy()
    lineno = lineno.copy()
    remark = remark.copy()
    auth = auth.copy()
    lddate = lddate.copy()


class Sensor(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('sta','chan','time','endtime'),)

    sta = sta.copy()
    chan = chan.copy()
    time = time.copy()
    endtime = endtime.copy()
    inid = inid.copy()
    chanid = chanid.copy()
    jdate = jdate.copy()
    calratio = calratio.copy()
    calper = calper.copy()
    tshift = tshift.copy()
    instant = instant.copy()
    lddate = lddate.copy()


class Site(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('sta','ondate'),)

    sta = sta.copy()
    ondate = ondate.copy()
    offdate = offdate.copy()
    lat = lat.copy()
    lon = lon.copy()
    elev = elev.copy()
    staname = staname.copy()
    statype = statype.copy()
    refsta = refsta.copy()
    dnorth = dnorth.copy()
    deast = deast.copy()
    lddate = lddate.copy()


class Sitechan(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (UniqueConstraint('sta','chan','ondate'),
                PrimaryKeyConstraint('chanid'),)

    sta = sta.copy()
    chan = chan.copy()
    ondate = ondate.copy()
    chanid = chanid.copy()
    offdate = offdate.copy()
    ctype = ctype.copy()
    edepth = edepth.copy()
    hang = hang.copy()
    vang = vang.copy()
    descrip = descrip.copy()
    lddate = lddate.copy()


class Sregion(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('srn'),)

    srn = srn.copy()
    srname = srname.copy()
    lddate = lddate.copy()


class Stamag(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('magid', 'sta', 'arid'),)

    magid = magid.copy()
    ampid = ampid.copy()
    sta = sta.copy()
    arid = arid.copy()
    orid = orid.copy()
    evid = evid.copy()
    phase = phase.copy()
    delta = delta.copy()
    magtype = magtype.copy()
    magnitude = magnitude.copy()
    uncertainty = uncertainty.copy()
    magres = magres.copy()
    magdef = magdef.copy()
    mmodel = mmodel.copy()
    auth = auth.copy()
    commid = commid.copy()
    lddate = lddate.copy()


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

    sta = sta.copy()
    chan = chan.copy()
    time = time.copy()
    wfid = wfid.copy()
    chanid = chanid.copy()
    jdate = jdate.copy()
    endtime = endtime.copy()
    nsamp = nsamp.copy()
    samprate = samprate.copy()
    calib = calib.copy()
    calper = calper.copy()
    instype = instype.copy()
    segtype = segtype.copy()
    datatype = datatype.copy()
    clip = clip.copy()
    dir = dir.copy()
    dfile = dfile.copy()
    foff = foff.copy()
    commid = commid.copy()
    lddate = lddate.copy()


class Wftag(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('tagid'),
                UniqueConstraint('tagname','tagid','wfid'),)

    tagname = tagname.copy()
    tagid = tagid.copy()
    wfid = wfid.copy()
    lddate = lddate.copy()


