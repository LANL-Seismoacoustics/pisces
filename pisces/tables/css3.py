from pisces.schema.util import CoreTable
import pisces.schema.css3 as css3


class Affiliation(css3.Affiliation):
    __tablename__ = 'affiliation'

class Amplitude(css3.Amplitude):
    __tablename__ = 'amplitude'

class Arrival(css3.Arrival):
    __tablename__ = 'arrival'

class Assoc(css3.Assoc):
    __tablename__ = 'assoc'

class Event(css3.Event):
    __tablename__ = 'event'

class Gregion(css3.Gregion):
    __tablename__ = 'gregion'

class Instrument(css3.Instrument):
    __tablename__ = 'instrument'

class Lastid(css3.Lastid):
    __tablename__ = 'lastid'

class Netmag(css3.Netmag):
    __tablename__ = 'netmag'

class Network(css3.Network):
    __tablename__ = 'network'

class Origerr(css3.Origerr):
    __tablename__ = 'origerr'

class Origin(css3.Origin):
    __tablename__ = 'origin'

class Remark(css3.Remark):
    __tablename__ = 'remark'

class Sensor(css3.Sensor):
    __tablename__ = 'sensor'

class Site(css3.Site):
    __tablename__ = 'site'

class Sitechan(css3.Sitechan):
    __tablename__ = 'sitechan'

class Sregion(css3.Sregion):
    __tablename__ = 'sregion'

class Stamag(css3.Stamag):
    __tablename__ = 'stamag'

class Wfdisc(css3.Wfdisc):
    __tablename__ = 'wfdisc'

class Wftag(css3.Wftag):
    __tablename__ = 'wftag'


CORETABLES = {'affiliation': CoreTable('affiliation', css3.Affiliation, Affiliation),
              'arrival': CoreTable('arrival', css3.Arrival, Arrival),
              'assoc': CoreTable('assoc', css3.Assoc, Assoc),
              'event': CoreTable('event', css3.Event, Event),
              'instrument': CoreTable('instrument', css3.Instrument, Instrument),
              'lastid': CoreTable('lastid', css3.Lastid, Lastid),
              'origin': CoreTable('origin', css3.Origin, Origin),
              'site': CoreTable('site', css3.Site, Site),
              'sitechan': CoreTable('sitechan', css3.Sitechan, Sitechan),
              'wfdisc': CoreTable('wfdisc', css3.Wfdisc, Wfdisc)}
