# Converted to Python 3.5.2 on 01-25-17
# by: Jeremy Webster


# coding: utf-8
"""
Core columns and abstract classes representing the KB Core seismic schema.

ORM classes that inherit from these classes are guaranteed primary and unique
keys, column info dictionaries, and schema-qualified __tablename__ .

Examples
--------
Define a site class that points to a 'TA_site' table.

>>> import pisces.schema.kbcore as kb
>>>
>>> class Site(kb.Site):
>>>     __tablename__ = 'TA_site'

Define a site class that points to a 'jkmacc.my_site' table.

>>> import pisces.schema.kbcore as kb
>>>
>>> class Site(kb.Site):
>>>     __tablename__ = 'jkmacc.my_site'

Create this table, if it doesn't exist.

>>> import sqlalchemy as sa
>>> e = sa.create_engine('sqlite:///my.sqlite')
>>> if not Site.__table__.exists(e)
>>>     Site.__table__.create(e)

Define a new abstract class in this schema.

>>> import sqlalchemy as sa
>>> from sqlalchemy.ext.declarative import declared_attr
>>> import pisces.schema.kbcore as kb
>>>
>>> def strparse(s):
>>>     return s.strip()
>>>
>>> class Beam(kb.Base):
>>>     __abstract__ = True
>>>     @declared_attr
>>>     def __table_args__(cls):
>>>         return (sa.PrimaryKeyConstraint('wfid'),)
>>>
>>>     wfid = kb.wfid._copy()
>>>     azimuth = kb.azimuth._copy()
>>>     slo = sa.Column(Float(24),
>>>         info={'default': -1.0, 'parse': float, 'width': 7, 'format': '7.4f'})
>>>     filter = sa.Column(String(30),
>>>         info={'default': '-', 'parse': strparse, 'width': 30, 'format': '30.30s'})
>>>     recipe = sa.Column(String(15),
>>>         info={'default': '-', 'parse': strparse, 'width': 15, 'format': '15.15s'})
>>>     algorithm = kb.algorithm._copy()
>>>     auth = kb.auth._copy()
>>>     lddate = kb.lddate._copy()

"""
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Integer
from sqlalchemy import Column
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declared_attr

from pisces.schema.util import PiscesMeta
from pisces.schema.util import parse_str, parse_int, parse_float
from pisces.io.trace import wfdisc2trace

# TODO: check __table_args__ syntax for final empty {}
# TODO: use http://docs.sqlalchemy.org/en/rel_0_8/orm/extensions/hybrid.html?

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
# NOTE: column names are not defined here, they are assigned during declarative
#       table definitions.  i.e. amp.name is None until it is used later.  This
#       allows recycling columns as different names, like sta1 = sta._copy().

# TODO: write a parser that gets the width (and type?) from info['format']

# specialized string parsing functions

# TODO: use dateutil module to handle wildcard characters, etc.?
# https://docs.python.org/2.7/library/datetime.html#strftime-strptime-behavior
# https://docs.python.org/2/library/string.html#format-specification-mini-language
DATEFMT = '%Y-%m-%d %H:%M:%S'


def dtfn(s):
    try:
        val = datetime.strptime(s, DATEFMT)
    except ValueError:
        val = None
    return val


algorithm = Column(String(15),
                   info={'default': '-', 'parse': parse_str, 'dtype': 'a15', 'width': 15, 'format': '15.15s'})

amp = Column(Float(24),
             info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 11, 'format': '11.2f'})

ampid = Column(Integer, nullable=False,
               info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})

amptime = Column(Float(53), info={'default': -9999999999.999, 'parse': parse_float,
                                  'dtype': 'float', 'width': 17, 'format': '17.5f'})

amptype = Column(String(8),
                 info={'default': '-', 'parse': parse_str, 'dtype': 'a8', 'width': 8, 'format': '8.8s'})

arid = Column(Integer,
              info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})

auth = Column(String(20),
              info={'default': '-', 'parse': parse_str, 'dtype': 'a20', 'width': 20, 'format': '20.20s'})

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
                info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})

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

endtime = Column(Float(53), info={'default': 9999999999.999,
                                  'parse': parse_float, 'dtype': 'float', 'width': 17, 'format': '17.5f'})

esaz = Column(Float(24),
              info={'default': -1, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})

etype = Column(String(7),
               info={'default': '-', 'parse': parse_str, 'dtype': 'a7', 'width': 7, 'format': '7.7s'})

evid = Column(Integer,
              info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})

evname = Column(String(32),
                info={'default': '-', 'parse': parse_str, 'dtype': 'a32', 'width': 32, 'format': '32.32s'})

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
             info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 11, 'format': '11.6f'})

lddate = Column(DateTime, nullable=False, onupdate=datetime.now,
                info={'default': datetime.now, 'parse': dtfn, 'dtype': 'O', 'width': 19, 'format': DATEFMT})

lineno = Column(Integer,
                info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '8d'})

logat = Column(Float(24),
               info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})

lon = Column(Float(53),
             info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 11, 'format': '11.6f'})

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
              info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})

ml = Column(Float(24),
            info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})

mlid = Column(Integer,
              info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})

ms = Column(Float(24),
            info={'default': -999.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})

msid = Column(Integer,
              info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})

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
              info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})

parid = Column(Integer,
               info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})

per = Column(Float(24),
             info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.2f'})

phase = Column(String(8),
               info={'default': '-', 'parse': parse_str, 'dtype': 'a8', 'width': 8, 'format': '8.8s'})

prefor = Column(Integer,
                info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 8, 'format': '9d'})

qual = Column(String(1),
              info={'default': '-', 'parse': parse_str, 'dtype': 'a1', 'width': 1, 'format': '1.1s'})

rect = Column(Float(24),
              info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 7, 'format': '7.3f'})

refsta = Column(String(6),
                info={'default': '-', 'parse': parse_str, 'dtype': 'str', 'width': 6, 'format': '6.6s'})

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
               info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})

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
              info={'default': -1, 'parse': parse_int, 'dtype': 'int', 'width': 9, 'format': '9d'})

wgt = Column(Float(24),
             info={'default': -1.0, 'parse': parse_float, 'dtype': 'float', 'width': 6, 'format': '6.3f'})


class Affiliation(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('net', 'sta', 'time'),)

    net = net._copy()
    sta = sta._copy()
    time = time._copy()
    endtime = endtime._copy()
    lddate = lddate._copy()


class Amplitude(Base):
    __abstract__ = True

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
                UniqueConstraint('sta', 'time', 'chan', 'iphase', 'auth'),)

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
        return (PrimaryKeyConstraint('arid', 'orid'), UniqueConstraint('arid'),)

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
        return (PrimaryKeyConstraint('evid'), UniqueConstraint('prefor'),)
    
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


# TODO: implement class-wide generator expressions on keyvalues.
#   https://groups.google.com/forum/#!topic/sqlalchemy/XksPIVYOdSU
# or something else
# http://stackoverflow.com/questions/10494033/setting-sqlalchemy-autoincrement-start-value
# @attr_generate
class Lastid(Base):
    """
    Store last id values.

    """
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('keyname'), UniqueConstraint('keyname', 'keyvalue'),)

    def __next__(self):
        self.keyvalue += 1
        return self.keyvalue

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

    net = net._copy()
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
        return (UniqueConstraint('lat', 'lon', 'depth', 'time', 'auth'), PrimaryKeyConstraint('orid'),)

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
        return (PrimaryKeyConstraint('commid', 'lineno'),)

    commid = commid._copy()
    lineno = lineno._copy()
    remark = remark._copy()
    lddate = lddate._copy()


class Sensor(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('sta', 'chan', 'time', 'endtime'),)

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
        return (PrimaryKeyConstraint('sta', 'ondate'),)

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
        return (UniqueConstraint('sta', 'chan', 'ondate'),
                PrimaryKeyConstraint('chanid'))

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

    srn = srn._copy()
    srname = srname._copy()
    lddate = lddate._copy()


class Stamag(Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return (PrimaryKeyConstraint('magid', 'sta', 'arid'),)

    magid = magid._copy()
    ampid = ampid._copy()
    sta = sta._copy()
    arid = arid._copy()
    orid = orid._copy()
    evid = evid._copy()
    phase = phase._copy()
    delta = delta._copy()
    magtype = magtype._copy()
    magnitude = magnitude._copy()
    uncertainty = uncertainty._copy()
    magres = magres._copy()
    magdef = magdef._copy()
    mmodel = mmodel._copy()
    auth = auth._copy()
    commid = commid._copy()
    lddate = lddate._copy()


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
        return (PrimaryKeyConstraint('tagname', 'tagid', 'wfid'),)

    tagname = tagname._copy()
    tagid = tagid._copy()
    wfid = wfid._copy()
    lddate = lddate._copy()


# possibly useful indexes
# To add, use Index.create(engine)
# ix_affiliation_stanet = Index(u'ix_affiliation_stanet',
#                              Affiliation.__table__.c.sta,
#                              Affiliation.__table__.c.net)
#
# ix_amplitude_uk = Index(u'ix_amplitude_uk',
#                        Amplitude.__table__.c.arid,
#                        Amplitude.__table__.c.amptime,
#                        Amplitude.__table__.c.amptype,
#                        Amplitude.__table__.c.auth,
#                        Amplitude.__table__.c.chan,
#                        Amplitude.__table__.c.deltaf,
#                        Amplitude.__table__.c.duration,
#                        Amplitude.__table__.c.parid,
#                        Amplitude.__table__.c.per,
#                        Amplitude.__table__.c.time)
#
# ix_arrival_uk = Index(u'ix_arrival_uk',
#                      Arrival.__table__.c.time,
#                      Arrival.__table__.c.sta,
#                      Arrival.__table__.c.chan,
#                      Arrival.__table__.c.iphase,
#                      Arrival.__table__.c.auth)
#
# ix_event_evid_prefor = Index(u'ix_event_evid_prefor',
#                             Event.__table__.c.evid,
#                             Event.__table__.c.prefor)
#
# ix_instrument_uk = Index(u'ix_instrument_uk',
#                         Instrument.__table__.c.dfile,
#                         Instrument.__table__.c.dir,
#                         Instrument.__table__.c.instype,
#                         Instrument.__table__.c.ncalib,
#                         Instrument.__table__.c.samprate)
#
# ix_netmaguk = Index(u'ix_netmaguk',
#                    Netmag.__table__.c.orid,
#                    Netmag.__table__.c.magtype,
#                    Netmag.__table__.c.auth)
#
# ix_network_uk = Index(u'ix_network_uk',
#                      Network.__table__.c.auth,
#                      Network.__table__.c.netname)
#
# ix_originautheviduk = Index(u'ix_originautheviduk',
#                            Origin.__table__.c.evid,
#                            Origin.__table__.c.auth)
#
# ix_origin_uk = Index(u'origin_uk',
#                     Origin.__table__.c.lat,
#                     Origin.__table__.c.lon,
#                     Origin.__table__.c.depth,
#                     Origin.__table__.c.time,
#                     Origin.__table__.c.auth)
#
# ix_b_newsite_onoff_ix = Index(u'ix_b_newsite_onoff',
#                              Site.__table__.c.ondate,
#                              Site.__table__.c.offdate)
#
# ix_site = Index(u'ix_site',
#                Site.__table__.c.sta,
#                Site.__table__.c.ondate,
#                Site.__table__.c.offdate)
#
# ix_sitechan_uk = Index(u'ix_sitechan_uk',
#                       Sitechan.__table__.c.sta,
#                       Sitechan.__table__.c.chan,
#                       Sitechan.__table__.c.ondate)
#
# ix_wfdisc_dirdfile = Index(u'ix_wfdisc_dirdfile',
#                           Wfdisc.__table__.c.dfile,
#                           Wfdisc.__table__.c.dir,
#                           Wfdisc.__table__.c.foff)
#
# ix_wfdisc = Index(u'ix_wfdisc',
#                  Wfdisc.__table__.c.sta,
#                  Wfdisc.__table__.c.jdate,
#                  Wfdisc.__table__.c.time,
#                  Wfdisc.__table__.c.endtime,
#                  Wfdisc.__table__.c.wfid)
#
# ix_wfdisc_uk = Index(u'ix_wfdisc_uk',
#                     Wfdisc.__table__.c.sta,
#                     Wfdisc.__table__.c.chan,
#                     Wfdisc.__table__.c.time)
#
# ix_wfdisc_chanid_instype = Index(u'ix_wfdisc_chanid_instype',
#                                 Wfdisc.__table__.c.chanid,
#                                 Wfdisc.__table__.c.instype)
