from pisces.schema.util import CoreTable
import pisces.schema.antelope as antelope


class Affiliation(antelope.Affiliation):
    __tablename__ = 'affiliation'

class Amplitude(antelope.Amplitude):
    __tablename__ = 'amplitude'

class Arrival(antelope.Arrival):
    __tablename__ = 'arrival'

class Assoc(antelope.Assoc):
    __tablename__ = 'assoc'

class Event(antelope.Event):
    __tablename__ = 'event'

class Gregion(antelope.Gregion):
    __tablename__ = 'gregion'

class Instrument(antelope.Instrument):
    __tablename__ = 'instrument'

class Lastid(antelope.Lastid):
    __tablename__ = 'lastid'

class Netmag(antelope.Netmag):
    __tablename__ = 'netmag'

class Network(antelope.Network):
    __tablename__ = 'network'

class Origerr(antelope.Origerr):
    __tablename__ = 'origerr'

class Origin(antelope.Origin):
    __tablename__ = 'origin'

class Remark(antelope.Remark):
    __tablename__ = 'remark'

class Sensor(antelope.Sensor):
    __tablename__ = 'sensor'

class Site(antelope.Site):
    __tablename__ = 'site'

class Sitechan(antelope.Sitechan):
    __tablename__ = 'sitechan'

class Sregion(antelope.Sregion):
    __tablename__ = 'sregion'

class Stamag(antelope.Stamag):
    __tablename__ = 'stamag'

class Wfdisc(antelope.Wfdisc):
    __tablename__ = 'wfdisc'

class Wftag(antelope.Wftag):
    __tablename__ = 'wftag'


CORETABLES = {'affiliation': CoreTable('affiliation', antelope.Affiliation, Affiliation),
              'arrival': CoreTable('arrival', antelope.Arrival, Arrival),
              'assoc': CoreTable('assoc', antelope.Assoc, Assoc),
              'event': CoreTable('event', antelope.Event, Event),
              'instrument': CoreTable('instrument', antelope.Instrument, Instrument),
              'lastid': CoreTable('lastid', antelope.Lastid, Lastid),
              'origin': CoreTable('origin', antelope.Origin, Origin),
              'site': CoreTable('site', antelope.Site, Site),
              'sitechan': CoreTable('sitechan', antelope.Sitechan, Sitechan),
              'wfdisc': CoreTable('wfdisc', antelope.Wfdisc, Wfdisc)}
