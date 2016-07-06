from pisces.schema.util import CoreTable
import pisces.schema.kbcore as kb


class Affiliation(kb.Affiliation):
    __tablename__ = 'affiliation'

class Amplitude(kb.Amplitude):
    __tablename__ = 'amplitude'

class Arrival(kb.Arrival):
    __tablename__ = 'arrival'

class Assoc(kb.Assoc):
    __tablename__ = 'assoc'

class Event(kb.Event):
    __tablename__ = 'event'

class Gregion(kb.Gregion):
    __tablename__ = 'gregion'

class Instrument(kb.Instrument):
    __tablename__ = 'instrument'

class Lastid(kb.Lastid):
    __tablename__ = 'lastid'

class Netmag(kb.Netmag):
    __tablename__ = 'netmag'

class Network(kb.Network):
    __tablename__ = 'network'

class Origerr(kb.Origerr):
    __tablename__ = 'origerr'

class Origin(kb.Origin):
    __tablename__ = 'origin'

class Remark(kb.Remark):
    __tablename__ = 'remark'

class Sensor(kb.Sensor):
    __tablename__ = 'sensor'

class Site(kb.Site):
    __tablename__ = 'site'

class Sitechan(kb.Sitechan):
    __tablename__ = 'sitechan'

class Sregion(kb.Sregion):
    __tablename__ = 'sregion'

class Stamag(kb.Stamag):
    __tablename__ = 'stamag'

class Wfdisc(kb.Wfdisc):
    __tablename__ = 'wfdisc'

class Wftag(kb.Wftag):
    __tablename__ = 'wftag'

CORETABLES = {'affiliation': CoreTable('affiliation', kb.Affiliation, Affiliation),
              'arrival': CoreTable('arrival', kb.Arrival, Arrival),
              'assoc': CoreTable('assoc', kb.Assoc, Assoc),
              'event': CoreTable('event', kb.Event, Event),
              'instrument': CoreTable('instrument', kb.Instrument, Instrument),
              'lastid': CoreTable('lastid', kb.Lastid, Lastid),
              'origin': CoreTable('origin', kb.Origin, Origin),
              'site': CoreTable('site', kb.Site, Site),
              'sitechan': CoreTable('sitechan', kb.Sitechan, Sitechan),
              'wfdisc': CoreTable('wfdisc', kb.Wfdisc, Wfdisc)}
