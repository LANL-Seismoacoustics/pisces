# Converted to Python 3.5.2 on 01-25-17
# by: Jeremy Webster

# coding: utf-8
"""
Center for Seismic Studies relational database schema 3.0 (CSS3.0)


"""
from datetime import datetime
from sqlalchemy import DateTime, Float, String, Integer
from sqlalchemy import Column
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declared_attr

from obspy.core import UTCDateTime
from pisces.schema.util import PiscesMeta
from pisces.schema.util import parse_int, parse_float, parse_str

from pisces.io.trace import wfdisc2trace
from copy import deepcopy as dc

Base = declarative_base(metaclass=PiscesMeta, constructor=None)

# COLUMN DEFINITIONS
# Generic SQLA types, compatible with different backends
# !! info dictionary defines the external representations (NumPy, text files)
#   and default values for the mapped class representation.
#
# XXX: for numeric types, maximum width is not enforced!
#
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
               info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})

amptime = Column(Float(53),
                 info={'default': -9999999999.999, 'parse': parse_float, 'dtype': 'float', 'width': 17, 'format': '17.5f'})

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

dist = Column(Float(24),
              info={'default': -1, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})

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

endtime = Column(Float(53),
                 info={'default': 9999999999.999, 'parse': parse_float, 'dtype': 'float', 'width': 17, 'format': '17.5f'})

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

imb = Column(Float(24),
             info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})

iml = Column(Float(24),
             info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})

ims = Column(Float(24),
             info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})

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

lat = Column(Float(24),
             info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})

lddate = Column(DateTime, nullable=False, onupdate=datetime.now,
                info={'default': datetime.now, 'parse': dtfn, 'dtype': 'O', 'width': 17, 'format': DATEFMT})

lineno = Column(Integer,
                info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})

location = Column(String(32),
                  info={'default': '-', 'parse': parse_str, 'dtype': 'a32', 'width': 32, 'format': '32.32s'})

logat = Column(Float(24),
               info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})

lon = Column(Float(24),
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
              info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})

smajax = Column(Float(24),
                info={'default': -1, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})

sminax = Column(Float(24),
                info={'default': -1, 'parse': parse_float, 'dtype': 'float', 'width': 9, 'format': '9.4f'})

snr = Column(Float(24),
             info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 10, 'format': '10.2f'})

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
               info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})

tagname = Column(String(8),
                 info={'default': '-', 'parse': parse_str, 'dtype': 'a8', 'width': 8, 'format': '8.8s'})

time = Column(Float(53),
              info={'default': -9999999999.999, 'parse': parse_float, 'dtype': 'float', 'width': 17, 'format': '17.5f'})

timedef = Column(String(1), info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})

timeres = Column(Float(24),
                 info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 8, 'format': '8.3f'})

tshift = Column(Float(24),
                info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 6, 'format': '6.2f'})

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
        return (PrimaryKeyConstraint('net', 'sta'),)

    net = dc(net)
    sta = dc(sta)
    lddate = dc(lddate)


class Amplitude(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('ampid'),)

    ampid = dc(ampid)
    arid = dc(arid)
    parid = dc(parid)
    chan = dc(chan)
    amp = dc(amp)
    per = dc(per)
    snr = dc(snr)
    amptime = dc(amptime)
    time = dc(time)
    duration = dc(duration)
    deltaf = dc(deltaf)
    amptype = dc(amptype)
    units = dc(units)
    clip = dc(clip)
    inarrival = dc(inarrival)
    auth = dc(auth)
    lddate = dc(lddate)


class Arrival(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('arid'),
                UniqueConstraint('sta', 'time', 'chan', 'iphase', 'auth'),)

    sta = dc(sta)
    time = dc(time)
    arid = dc(arid)
    jdate = dc(jdate)
    stassid = dc(stassid)
    chanid = dc(chanid)
    chan = dc(chan)
    iphase = dc(iphase)
    stype = dc(stype)
    deltim = dc(deltim)
    azimuth = dc(azimuth)
    delaz = dc(delaz)
    slow = dc(slow)
    delslo = dc(delslo)
    ema = dc(ema)
    rect = dc(rect)
    amp = dc(amp)
    per = dc(per)
    logat = dc(logat)
    clip = dc(clip)
    fm = dc(fm)
    snr = dc(snr)
    qual = dc(qual)
    auth = dc(auth)
    commid = dc(commid)
    lddate = dc(lddate)


class Assoc(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('arid', 'orid'), UniqueConstraint('arid'), )

    arid = dc(arid)
    orid = dc(orid)
    sta = dc(sta)
    phase = dc(phase)
    belief = dc(belief)
    delta = dc(delta)
    seaz = dc(seaz)
    esaz = dc(esaz)
    timeres = dc(timeres)
    timedef = dc(timedef)
    azres = dc(azres)
    azdef = dc(azdef)
    slores = dc(slores)
    slodef = dc(slodef)
    emares = dc(emares)
    wgt = dc(wgt)
    vmodel = dc(vmodel)
    commid = dc(commid)
    lddate = dc(lddate)


class Event(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('evid'), UniqueConstraint('prefor'),)

    evid = dc(evid)
    evname = dc(evname)
    prefor = dc(prefor)
    auth = dc(auth)
    commid = dc(commid)
    lddate = dc(lddate)


class Gregion(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('grn'),)

    grn = dc(grn)
    grname = dc(grname)
    lddate = dc(lddate)


class Instrument(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('inid'),)

    inid = dc(inid)
    insname = dc(insname)
    instype = dc(instype)
    band = dc(band)
    digital = dc(digital)
    samprate = dc(samprate)
    ncalib = dc(ncalib)
    ncalper = dc(ncalper)
    dir = dc(dir)
    dfile = dc(dfile)
    rsptype = dc(rsptype)
    lddate = dc(lddate)


class Lastid(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('keyname'), UniqueConstraint('keyname', 'keyvalue'),)

    keyname = dc(keyname)
    keyvalue = dc(keyvalue)
    lddate = dc(lddate)


class Netmag(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('magid'),
                UniqueConstraint('magid', 'orid'),)

    magid = dc(magid)
    net = dc(net)
    orid = dc(orid)
    evid = dc(evid)
    magtype = dc(magtype)
    nsta = dc(nsta)
    magnitude = dc(magnitude)
    uncertainty = dc(uncertainty)
    auth = dc(auth)
    commid = dc(commid)
    lddate = dc(lddate)


class Network(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('net'),)

    net = dc(net)
    netname = dc(netname)
    nettype = dc(nettype)
    auth = dc(auth)
    commid = dc(commid)
    lddate = dc(lddate)


class Origerr(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('orid'),)

    orid = dc(orid)
    sxx = dc(sxx)
    syy = dc(syy)
    szz = dc(szz)
    stt = dc(stt)
    sxy = dc(sxy)
    sxz = dc(sxz)
    syz = dc(syz)
    stx = dc(stx)
    sty = dc(sty)
    stz = dc(stz)
    sdobs = dc(sdobs)
    smajax = dc(smajax)
    sminax = dc(sminax)
    strike = dc(strike)
    sdepth = dc(sdepth)
    stime = dc(stime)
    conf = dc(conf)
    commid = dc(commid)
    lddate = dc(lddate)


class Origin(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (UniqueConstraint('lat', 'lon', 'depth', 'time', 'auth'), PrimaryKeyConstraint('orid'))

    lat = dc(lat)
    lon = dc(lon)
    depth = dc(depth)
    time = dc(time)
    orid = dc(orid)
    evid = dc(evid)
    jdate = dc(jdate)
    nass = dc(nass)
    ndef = dc(ndef)
    ndp = dc(ndp)
    grn = dc(grn)
    srn = dc(srn)
    etype = dc(etype)
    depdp = dc(depdp)
    dtype = dc(dtype)
    mb = dc(mb)
    mbid = dc(mbid)
    ms = dc(ms)
    msid = dc(msid)
    ml = dc(ml)
    mlid = dc(mlid)
    algorithm = dc(algorithm)
    auth = dc(auth)
    commid = dc(commid)
    lddate = dc(lddate)


class Remark(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('commid', 'lineno'),)

    commid = dc(commid)
    lineno = dc(lineno)
    remark = dc(remark)
    lddate = dc(lddate)


class Sensor(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('sta', 'chan', 'time', 'endtime'),)

    sta = dc(sta)
    chan = dc(chan)
    time = dc(time)
    endtime = dc(endtime)
    inid = dc(inid)
    chanid = dc(chanid)
    jdate = dc(jdate)
    calratio = dc(calratio)
    calper = dc(calper)
    tshift = dc(tshift)
    instant = dc(instant)
    lddate = dc(lddate)


class Site(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('sta', 'ondate'),)

    sta = dc(sta)
    ondate = dc(ondate)
    offdate = dc(offdate)
    lat = dc(lat)
    lon = dc(lon)
    elev = dc(elev)
    staname = dc(staname)
    statype = dc(statype)
    refsta = dc(refsta)
    dnorth = dc(dnorth)
    deast = dc(deast)
    lddate = dc(lddate)


class Sitechan(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (UniqueConstraint('sta', 'chan', 'ondate'),
                PrimaryKeyConstraint('chanid'),)

    sta = dc(sta)
    chan = dc(chan)
    ondate = dc(ondate)
    chanid = dc(chanid)
    offdate = dc(offdate)
    ctype = dc(ctype)
    edepth = dc(edepth)
    hang = dc(hang)
    vang = dc(vang)
    descrip = dc(descrip)
    lddate = dc(lddate)


class Sregion(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('srn'),)

    srn = dc(srn)
    srname = dc(srname)
    lddate = dc(lddate)


class Stamag(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('magid', 'sta'),)

    magid = dc(magid)
    sta = dc(sta)
    arid = dc(arid)
    orid = dc(orid)
    evid = dc(evid)
    phase = dc(phase)
    delta = dc(delta)
    magtype = dc(magtype)
    magnitude = dc(magnitude)
    uncertainty = dc(uncertainty)
    auth = dc(auth)
    commid = dc(commid)
    lddate = dc(lddate)
    
    
class Stassoc(Base):
    __abstract__ = True
    
    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('stassid'),)
        
    stassid = dc(stassid)
    sta = dc(sta)
    etype = dc(etype)
    location = dc(location)
    dist = dc(dist)
    azimuth = dc(azimuth)
    lat = dc(lat)
    lon = dc(lon)
    depth = dc(depth)
    time = dc(time)
    imb = dc(imb)
    ims = dc(ims)
    iml = dc(iml)
    auth = dc(auth)
    commid = dc(commid)
    lddate = dc(lddate)
        

class Wfdisc(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (UniqueConstraint('wfid', 'dir', 'dfile'), PrimaryKeyConstraint('wfid'),)

    def to_trace(self):
        """
        Read the wfdisc line into a Trace instance.  Minimal header.

        Returns
        -------
        obspy.Trace

        """
        return wfdisc2trace(self)

    sta = dc(sta)
    chan = dc(chan)
    time = dc(time)
    wfid = dc(wfid)
    chanid = dc(chanid)
    jdate = dc(jdate)
    endtime = dc(endtime)
    nsamp = dc(nsamp)
    samprate = dc(samprate)
    calib = dc(calib)
    calper = dc(calper)
    instype = dc(instype)
    segtype = dc(segtype)
    datatype = dc(datatype)
    clip = dc(clip)
    dir = dc(dir)
    dfile = dc(dfile)
    foff = dc(foff)
    commid = dc(commid)
    lddate = dc(lddate)


class Wftag(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('tagname', 'tagid', 'wfid'),)

    tagname = dc(tagname)
    tagid = dc(tagid)
    wfid = dc(wfid)
    lddate = dc(lddate)
