from pisces.schema.util import CoreTable
import pisces.schema.kbcore as kba


class Affiliation(kba.Affiliation):
    __tablename__ = 'affiliation'

class Amplitude(kba.Amplitude):
    __tablename__ = 'amplitude'

class Arrival(kba.Arrival):
    __tablename__ = 'arrival'

class Assoc(kba.Assoc):
    __tablename__ = 'assoc'

class Event(kba.Event):
    __tablename__ = 'event'

class Gregion(kba.Gregion):
    __tablename__ = 'gregion'

class Instrument(kba.Instrument):
    __tablename__ = 'instrument'

class Lastid(kba.Lastid):
    __tablename__ = 'lastid'

class Netmag(kba.Netmag):
    __tablename__ = 'netmag'

class Network(kba.Network):
    __tablename__ = 'network'

class Origerr(kba.Origerr):
    __tablename__ = 'origerr'

class Origin(kba.Origin):
    __tablename__ = 'origin'

class Remark(kba.Remark):
    __tablename__ = 'remark'

class Sensor(kba.Sensor):
    __tablename__ = 'sensor'

class Site(kba.Site):
    __tablename__ = 'site'

class Sitechan(kba.Sitechan):
    __tablename__ = 'sitechan'

class Sregion(kba.Sregion):
    __tablename__ = 'sregion'

class Stamag(kba.Stamag):
    __tablename__ = 'stamag'

class Wfdisc(kba.Wfdisc):
    __tablename__ = 'wfdisc'

class Wftag(kba.Wftag):
    __tablename__ = 'wftag'

CORETABLES = [CoreTable('affiliation', kba.Affiliation, kb.Affiliation),
              CoreTable('arrival', kba.Arrival, kb.Arrival),
              CoreTable('assoc', kba.Assoc, kb.Assoc),
              CoreTable('event', kba.Event, kb.Event),
              CoreTable('instrument', kba.Instrument, kb.Instrument),
              CoreTable('lastid', kba.Lastid, kb.Lastid),
              CoreTable('origin', kba.Origin, kb.Origin),
              CoreTable('site', kba.Site, kb.Site),
              CoreTable('sitechan', kba.Sitechan, kb.Sitechan),
              CoreTable('wfdisc', kba.Wfdisc, kb.Wfdisc)]


