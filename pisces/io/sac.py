"""
Conversions between SAC header variables and KB Core fields.

"""
#XXX: currently not working
#TODO: remove functions already in pisces.io.trace
#TODO: make everything just translate dictionaries, not classes
#TODO: change db.flatfile.KBTABLEDICT to use pisces.schema.util.get_infovals
import sys
import os
from collections import OrderedDict

from obspy.core import UTCDateTime, Trace, Stats, AttribDict
import obspy.core.util.geodetics as geod

import pisces.schema.kbcore as kb
from pisces.io.readwaveform import read_waveform
from pisces.io.util import _map_header, _buildhdr

# ObsPy default values
OBSPYDEFAULT = {'network': '',
                'station': '',
                'location': '',
                'channel': ''}


class Site(kb.Site):
    __tablename__ = 'site'

class Sitechan(kb.Sitechan):
    __tablename__ = 'sitechan'

class Affiliation(kb.Affiliation):
    __tablename__ = 'affiliation'

class Instrument(kb.Instrument):
    __tablename__ = 'instrument'

class Origin(kb.Origin):
    __tablename__ = 'origin'

class Event(kb.Event):
    __tablename__ = 'event'

class Assoc(kb.Assoc):
    __tablename__ = 'assoc'

class Arrival(kb.Arrival):
    __tablename__ = 'arrival'

class Wfdisc(kb.Wfdisc):
    __tablename__ = 'wfdisc'

# ------------------ CONVERT SAC HEADER DICTIONARY TO TABLES ------------#
# SAC default values
IDEFAULT = -12345
FDEFAULT = -12345.0 
SDEFAULT = '-12345  '
SLDEFAULT = '-12345          '
SACDEFAULT = {'a': FDEFAULT, 'az': FDEFAULT, 'b': FDEFAULT, 'baz': FDEFAULT,
         'cmpaz': FDEFAULT, 'cmpinc': FDEFAULT, 'delta': FDEFAULT, 
         'depmax': FDEFAULT, 'depmen': FDEFAULT, 'depmin': FDEFAULT, 
         'dist': FDEFAULT, 'e': FDEFAULT, 'evdp': FDEFAULT, 'evla': FDEFAULT, 
         'evlo': FDEFAULT, 'f': FDEFAULT, 'gcarc': FDEFAULT, 'idep': IDEFAULT, 
         'ievreg': IDEFAULT, 'ievtype': IDEFAULT, 'iftype': IDEFAULT, 
         'iinst': IDEFAULT, 'imagsrc': IDEFAULT, 'imagtyp': IDEFAULT,
         'int1': FDEFAULT, 'iqual': IDEFAULT, 'istreg': IDEFAULT, 
         'isynth': IDEFAULT, 'iztype': IDEFAULT, 'ka': SDEFAULT, 
         'kcmpnm': SDEFAULT, 'kdatrd': SDEFAULT, 'kevnm': SLDEFAULT, 
         'kf': SDEFAULT, 'khole': SDEFAULT, 'kinst': SDEFAULT,
         'knetwk': SDEFAULT, 'ko': SDEFAULT, 'kstnm': SDEFAULT, 'kt0': SDEFAULT,
         'kt1': SDEFAULT, 'kt2': SDEFAULT, 'kt3': SDEFAULT, 'kt4': SDEFAULT,
         'kt5': SDEFAULT, 'kt6': SDEFAULT, 'kt7': SDEFAULT, 'kt8': SDEFAULT,
         'kt9': SDEFAULT, 'kuser0': SDEFAULT, 'kuser1': SDEFAULT, 
         'kuser2': SDEFAULT, 'lcalda': IDEFAULT, 'leven': IDEFAULT, 
         'lovrok': IDEFAULT, 'lpspol': IDEFAULT, 'mag': FDEFAULT, 
         'nevid': IDEFAULT, 'norid': IDEFAULT, 'npts': IDEFAULT, 
         'nvhdr': IDEFAULT, 'nwfid': IDEFAULT, 'nzhour': IDEFAULT, 
         'nzjday': IDEFAULT, 'nzmin': IDEFAULT, 'nzmsec': IDEFAULT,
         'nzsec': IDEFAULT, 'nzyear': IDEFAULT, 'o': FDEFAULT, 
         'odelta': FDEFAULT, 'scale': FDEFAULT, 'stdp': FDEFAULT, 
         'stel': FDEFAULT, 'stla': FDEFAULT, 'stlo': FDEFAULT, 't0': FDEFAULT,
         't1': FDEFAULT, 't2': FDEFAULT, 't3': FDEFAULT, 't4': FDEFAULT, 
         't5': FDEFAULT, 't6': FDEFAULT, 't7': FDEFAULT, 't8': FDEFAULT, 
         't9': FDEFAULT, 'unused10': FDEFAULT, 'unused11': FDEFAULT, 
         'unused12': FDEFAULT, 'unused6': FDEFAULT, 'unused7': FDEFAULT,
         'unused8': FDEFAULT, 'unused9': FDEFAULT, 'user0': FDEFAULT, 
         'user1': FDEFAULT, 'user2': FDEFAULT, 'user3': FDEFAULT, 
         'user4': FDEFAULT, 'user5': FDEFAULT, 'user6': FDEFAULT, 
         'user7': FDEFAULT, 'user8': FDEFAULT, 'user9': FDEFAULT,
         'xmaximum': FDEFAULT, 'xminimum': FDEFAULT, 'ymaximum': FDEFAULT, 
         'yminimum': FDEFAULT}


# the following functions accept a SAC header dictionary, and return respective
# kbcore table instances, assumes default SAC header values set to None

def get_sac_reftime(tr):
    """
    Get UTCDateTime object from sac header dict.
    """
    # "nz" fields are not kept when ObsPy reads a SAC file.  They're used 
    # to make "starttime", then discarded.
    # t0 = nzyear + nzjday + nzhour + nzminute + nzsecond + nzmsec*1000
    # starttime = t0 + b
    # therefore: t0 = starttime - b
    if tr.stats.sac.b is SACDEFAULT['b']:
        t0 = tr.stats.starttime
    else:
        t0 = tr.stats.starttime - tr.stats.sac.b

    return t0

def sachdr2reftime(hdr):
    """Get SAC reference UTCDateTime from header dictionary.
    """
    # reftime = nzyear + nzjday + nzhour + nzminute + nzsecond + nzmsec*1000
    tdict = {'year': 1970, 'month': 1, 'day': 1, 'minute': 0, 'microsecond': 0}
    # for non-default values in hdr, return desired values, mapped to new keys
    mapdict = _map_header({'nzyear': 'year', 'nzjday':'julday', 'nzhour':'hour', 
                           'nzmin':'minute', 'nzsec':'second', 
                           'nzmsec':'microsecond'}, hdr, SACDEFAULT)
    tdict.update(mapdict)
    if tdict['microsecond']:
        tdict['microsecond'] *= 1000.
    
    #tdict = {}
    #tdict.update((key, val) for key, val in tmpdict.iteritems() \
    #        if val is not None)

    t0 = UTCDateTime(**tdict)


def tr2site(tr):
    """
    Provide an ObsPy Trace, get a filled site table instance, using available
    header.
    """
    sitedict = {}

    #1) from obspy header first
    if tr.stats.station:
        sitedict['sta'] = tr.stats.station

    #2) get from sac header
    try:
        sac2site = {'stla': 'lat', 'stlo': 'lon', 'stel': 'elev'}
        sitedict.update(_map_header(sac2site, tr.stats.sac, SACDEFAULT))
        try:            
            sitedict['elev'] /= 1000
        except KeyError:
            #no 'elev' 
            pass
    except (AttributeError, KeyError):
        # tr.stats has no "sac" attribute
        pass

    if sitedict:
        site = Site(**sitedict)
    else:
        site = None

    return site


def tr2sitechan(tr):
    """Provide a sac header dictionary, get a filled sitechan table instance."""

    #1) from obspy header
    sitechandict = _map_header({'station': 'sta', 'channel': 'chan'}, tr.stats, 
                                OBSPYDEFAULT)

    #2) from sac header
    try:
        sac2sitechan = {'cmpaz': 'hang', 'cmpinc': 'vang', 'stdp': 'edepth'}
        sitechandict.update(_map_header(sac2sitechan, tr.stats.sac, SACDEFAULT))
        try:           
            sitechandict['edepth'] /= 1000.
        except (TypeError, KeyError):
            #edepth is None or missing
            pass
    except (AttributeError, KeyError):
        # no tr.stats.sac
        pass

    if sitechandict:
        sitechan = Sitechan(**sitechandict)
    else:
        sitechan = None

    return sitechan
    

def tr2affiliation(tr):
    #1) from obspy header
    affildict = _map_header({'network': 'net', 'station': 'sta'}, tr.stats,
                             OBSPYDEFAULT)

    #2) from sac header
    try:
        sac2affiliation = {'knetwk': 'net', 'kstnm': 'sta'}
        affildict.update(_map_header(sac2affiliation, tr.stats.sac, SACDEFAULT))
    except (AttributeError, KeyError):
        # no tr.stats.sac or 'knetwk', etc.
        pass

    if affildict:
        affil = Affiliation(**affildict)
    else:
        affil = None

    return affil


def tr2instrument(tr):
    #TODO: investigate hdr['resp0-9'] values
    #1) from sac header
    instrdict = {'samprate': int(tr.stats.sampling_rate)}
    try:
        instrdict = _map_header({'kinst': 'ins', 'iinst': 'instype'}, 
                                tr.stats.sac, SACDEFAULT)
    except AttributeError:
        #no tr.stats.sac
        pass

    if instrdict:
        instr = Instrument(**instrdict)
    else:
        instr = None

    return instr


def tr2origin(tr):
    """
    Provide a sac header dictionary, get a filled origin table instance.
    A few things:
    1) If sac reference time isn't event-based, origin time is unknown
    2) magnitude is taken first from hdr['mag'], hdr['imagtyp'] if defined,
       then replaced by hdr['user0'],hdr['kuser0']
    3) sac moment, duration, and user-defined magnitude headers aren't
       put into the origin table
    4) origin.auth is taken first from hdr['imagsrc'], then replaced by
       hdr['kuser1'] if defined.  the imagsrc->auth translations are:

     * INEIC -> ISC:NEIC
     * IPDE -> PDE
     * IISC -> ISC
     * IBRK -> ISC:BERK
     * IUSGS, ICALTECH, ILLNL, IEVLOC, IJSOP, IUSER, IUNKNOWN -> unchanged 
    
    """
    # simple SAC translations
    sac2origin = {'evla': 'lat', 'evlo': 'lon', 'norid': 'orid', 
                  'nevid': 'evid', 'ievreg': 'grn', 'evdp': 'depth'}
    try:
        origindict = _map_header(sac2origin, tr.stats.sac, SACDEFAULT)
    except AttributeError:
        #no tr.stats.sac
        pass

    #depth
    try:
        origindict['depth'] = tr.stats.sac['evdp']/1000.
    except (TypeError, AttributeError):
        #evdp is None, or no tr.stats.sac
        pass

    #etype translations
    edict = {37: 'en', 38: 'ex', 39: 'ex', 40: 'qt', 41: 'qt', 42: 'qt', 
            43: 'ec', 72: 'me', 73: 'me', 74: 'me', 75: 'me', 76: 'mb',
            77: 'qt', 78: 'qt', 79: 'qt', 80: 'ex', 81: 'ex', 82: 'en',
            83: 'mc'}
    try:
        origindict['etype'] = edict[tr.stats.sac['ievtype']]
    except (AttributeError, KeyError):
        #ievtyp is None, or not a key in edict (e.g. sac default value)
        pass

    #1: 
    try:
        t = get_sac_reftime(tr)
        if tr.stats.sac['iztype'] == 11:
            #reference time is an origin time
            if tr.stats.sac.o is SACDEFAULT['o']:
                o = 0.0
            else:
                o = tr.stats.sac.o
            origindict['time'] = t.timestamp - o
            origindict['jdate'] = int((t-o).strftime('%Y%j'))
    except (AttributeError, KeyError):
        # no trace.stats.sac, no iztype
        pass

    #2: magnitude
    magdict = {52: 'mb', 53: 'ms', 54: 'ml'}
    try:
        origindict[magdict[tr.stats.sac['imagtyp']]] = tr.stats.sac['mag']
    except KeyError:
        #imagtyp is None or not a key in magdict
        pass

    # is kuser0 is a recognized magnitude type, overwrite mag
    #XXX: this is a LANL wfdisc2sac thing
    try:
        magtype = tr.stats.sac['kuser0'].strip()
        if magtype in magdict.values():
            origindict[magtype] = tr.stats.sac['user0']
    except AttributeError:
        #kuser0 is None
        pass

    #3: origin author
    authdict = {58: 'ISC:NEIC', 61: 'PDE', 62: 'ISC', 63: 'REB-ICD', 
            64: 'IUSGS', 65: 'ISC:BERK', 66: 'ICALTECH', 67: 'ILLNL',
            68: 'IEVLOC', 69: 'IJSOP', 70: 'IUSER', 71: 'IUNKNOWN'}
    try:
        origindict['auth'] = authdict[tr.stats.sac['imagsrc']]
    except KeyError:
        # imagsrc not in authdict (i.e. sac default value)
        pass

    #XXX: this is LANL wfdisc2sac thing.  maybe turn it off?
    if tr.stats.sac['kuser1']:
        origindict['auth'] = tr.stats.sac['kuser1']

    if origindict:
        origin = Origin(**origindict)
    else:
        origin = None

    return origin


def tr2event(tr):
    eventdict = {}
    try:
        eventdict.update(_map_header({'nevid': 'evid', 'kevnm': 'evname'},
                                tr.stats.sac, SACDEFAULT))
    except AttributeError:
        #no tr.stats.sac
        pass

    if eventdict:
        event = Event(**eventdict)
    else:
        event = None

    return event


def tr2assoc(tr, pickmap=None):
    """
    Takes a sac header dictionary, and produces a list of up to 10 
    Assoc instances. Header->phase mappings follow SAC2000, i.e.:

    * t0: P
    * t1: Pn
    * t2: Pg
    * t3: S
    * t4: Sn
    * t5: Sg
    * t6: Lg
    * t7: LR
    * t8: Rg
    * t9: pP

    An alternate mapping for some or all picks can be supplied, however, 
    as a dictionary of strings in the above form.  
    
    Note: arid values will not be filled in, so do:
    >>> for assoc in kbio.tables['assoc']:
            assoc.arid = lastarid+1
            lastarid += 1

    """
    pick2phase = {'t0': 'P', 't1': 'Pn', 't2': 'Pg', 't3': 'S',
    't4': 'Sn', 't5': 'Sg', 't6': 'Lg', 't7': 'LR', 't8': 'Rg',
    't9': 'pP'} 

    #overwrite defaults with supplied map
    if pickmap:
        pick2phase.update(pickmap)

    #geographic relations
    # obspy.read tries to calculate these values if lcalca is True and needed
    #header info is there, so we only need to try to if lcalca is False.
    #XXX: I just calculate it if no values are currently filled in.
    assocdict = {}
    try:
        assocdict.update(_map_header({'az': 'esaz', 'baz': 'seaz', 
                                      'gcarc': 'delta'}, tr.stats.sac, 
                                      SACDEFAULT))
    except AttributeError:
        # no tr.stats.sac
        pass

    #overwrite if any are None
    if not assocdict:
        try:
            delta = geod.locations2degrees(tr.stats.sac.stla, tr.stats.sac.stlo, 
                                           tr.stats.sac.evla, tr.stats.sac.evlo)
            m, seaz, esaz = geod.gps2DistAzimuth(tr.stats.sac.stla, 
                tr.stats.sac.stlo, tr.stats.sac.evla, tr.stats.sac.evlo)
            assocdict['esaz'] = esaz
            assocdict['seaz'] = seaz
            assocdict['delta'] = delta
        except (AttributeError, TypeError):
            #some sac header values are None
            pass

    if tr.stats.station:
        assocdict['sta'] = tr.stats.station

    assocdict.update(_map_header({'norid': 'orid'}, tr.stats.sac, SACDEFAULT))

    #now, do the phase arrival mappings
    #for each pick in hdr, make a separate dictionary containing assocdict plus
    #the new phase info.
    assocs = []
    for key in pick2phase:
        kkey = 'k' + key
        #if there's a value in t[0-9]
        if tr.stats.sac[key] != SACDEFAULT[key]:
            #if the phase name kt[0-9] is null
            if tr.stats.sac[kkey] == SACDEFAULT[kkey]:
                #take it from the map
                iassoc = {'phase': pick2phase[key]}
            else:
                #take it directly
                iassoc = {'phase': tr.stats.sac[kkey]}

            iassoc.update(assocdict)
            assocs.append(iassoc)

    return [Assoc(**assoc) for assoc in assocs]


def tr2arrival(tr, pickmap=None):
    """Similar to tr2assoc, but produces a list of up to 10 Arrival
    instances.  Same header->phase mapping applies, unless otherwise stated.

    """
    #puts t[0-9] times into arrival.time if they're not null
    #puts corresponding kt[0-9] phase name into arrival.iphase
    #if a kt[0-9] phase name is null and its t[0-9] values isn't,
    #phase names are pulled from the pick2phase dictionary
    pick2phase = {'t0': 'P', 't1': 'Pn', 't2': 'Pg', 't3': 'S',
    't4': 'Sn', 't5': 'Sg', 't6': 'Lg', 't7': 'LR', 't8': 'Rg',
    't9': 'pP'} 

    if pickmap:
        pick2phase.update(pickmap)

    #simple translations
    arrivaldict = {}
    if tr.stats.station:
        arrivaldict['sta'] = tr.stats.station
    if tr.stats.channel:
        arrivaldict['chan'] = tr.stats.channel

    #phases and arrival times
    t0 = get_sac_reftime(tr)
    arrivals = []
    for key in pick2phase:
        kkey = 'k' + key
        # if there's a value in t[0-9]
        if tr.stats.sac[key] != SACDEFAULT[key]:
            itime = t + tr.stats.sac[key]
            iarrival = {'time': itime.timestamp,
                        'jdate': int(itime.strftime('%Y%j'))}
            #if the phase name kt[0-9] is null
            if tr.stats.sac[kkey] == SACDEFAULT[kkey]:
                #take it from the pick2phase map
                iarrival['iphase'] = pick2phase[key]
            else:
                #take it directly
                iarrival['iphase'] = tr.stats.sac[kkey]

            iarrival.update(arrivaldict)
            arrivals.append(iassoc)

    return [Arrival(**arrival) for arrival in arrivals]


def tr2wfdisc(tr):
    """Produce wfdisc kbcore table instance from sac header dictionary.
    Clearly this will be a skeleton instance, as the all-important 'dir' and 
    'dfile' must be filled in later.

    Note: if you read a little-endian SAC file onto a big-endian machine, it
    seems that obspy.sac.sacio.SacIO.swap_byte_order has trouble.

    """
    # from obspy header
    wfdict = {}
    wfdict['nsamp'] = tr.stats.npts
    wfdict['time'] = tr.stats.starttime.timestamp
    wfdict['endtime'] = tr.stats.endtime.timestamp
    wfdict['jdate'] = int(tr.stats.starttime.strftime('%Y%j'))
    wfdict['samprate'] = int(tr.stats.sampling_rate)
    if tr.stats.station:
        wfdict['sta'] = tr.stats.station
    if tr.stats.channel: 
        wfdict['chan'] = tr.stats.channel
    if tr.stats.calib:
        wfdict['calib'] = tr.stats.calib

    #from sac header
    try:
        wfdict.update(_map_header({'nwfid': 'wfid'}, tr.stats.sac, SACDEFAULT))
        wfdict['foff'] = 634
        if sys.byteorder == 'little':
            wfdict['datatype'] = 'f4'
        else:
            wfdict['datatype'] = 't4'
    except AttributeError:
        #no tr.stats.sac
        pass

    return Wfdisc(**wfdict)


def trace2tables(tr, tables=None, schema='kbcore'):
    """
    Scrape ObsPy Trace headers into database table dictionary.
    Null values in Trace headers are not returned.

    Parameters
    ----------
    tr: Obspy.core.Trace
    tables: list, optional
        Table name strings to return. 
        Default, ['affiliation', 'arrival', 'assoc', 'event', 'instrument',
        'origin', 'site', 'sitechan', 'wfdisc']
    schema: string, optional
        'kbcore' or 'css'.  Default: 'kbcore'
        ***Not yet implemented***

    Returns
    -------
    dict
        Dictionary of table objects.  tables['arrival'] and tables['assoc']
        return (possibly empty) _lists_ of table objects.  If only default 
        values are found for a table, it is omitted.

    Notes
    -----
    Some things must be checked or filled in before adding to a database:
    - affiliation.time, endtime
    - arrival.arid
    - assoc.orid, arid
    - event.prefor, evid
    - instrument.inid, dir, dfile, rsptype
    - site.ondate
    - sitechan.ondate, chanid
    - wfdisc.dir, dfile, foff, datetype, wfid

    """
    fns = {'affiliation': tr2affiliation,
           'arrival': tr2arrival,
           'assoc': tr2assoc,
           'event': tr2event,
           'instrument': tr2instrument,
           'origin': tr2origin,
           'site': tr2site,
           'sitechan': tr2sitechan,
           'wfdisc': tr2wfdisc}

    if tables is None:
        tables = fns.keys()

    t = AttribDict()
    #for table, fn in fns.iteritems():
    for table in tables:
        ifn = fns[table]
        itab = ifn(tr)
        if itab:
            t[table] = ifn(tr)

    return t


#----------------- CONVERT TABLES TO SAC HEADER DICTIONARY ---------------#
#TODO: make these functions able to gracefully handle None values as inputs
def site2sachdr(s):
    """
    Accepts a fielded site table row and returns a dictionary of corresponding
    sac header field/value pairs.
    """
    keymap = {'stel': 'elev', 'stal': 'lat', 'stlo': 'lon'}
    hdr = _buildhdr(keymap, s)
    return hdr

def sitechan2sachdr(sc):
    keymap = {'cmpaz': 'hang', 'cmpinc': 'vang'}
    hdr = _buildhdr(keymap, sc)
    return hdr

def affiliation2sachdr(af):
    keymap = {'network': 'net'}
    hdr = _buildhdr(keymap, af)
    return hdr

def instrument2sachdr(ins):
    return {}

def origin2sachdr(o):
    """
    Accepts a fielded origin table record and produces a dictionary of
    corresponding sac header field/value pairs.
    """
    keymap = {'evdp': 'depth', 'evla': 'lat', 'evlo': 'lon', 'kuser1': 'auth',
        'nevid': 'evid', 'norid': 'orid', 'user0': 'mb'}
    hdr = _buildhdr(keymap, o)
    return hdr
 
def event2sachdr(evt):
    return {}

def assoc2sachdr(asc):
    return {}

def arrival2sachdr(ar):
    return {}


def wfdisc2sachdr(wf):
    pass


#functions that accept a table, return a dictionary of sac header values
#the order of this dictionary matters
KB2SAC = OrderedDict({'site': site2sachdr,
          'sitechan': sitechan2sachdr,
          'wfdisc': wfdisc2sachdr,
          'affiliation': affiliation2sachdr,
          'instrument': instrument2sachdr,
          'origin': origin2sachdr,
          'event': event2sachdr,
          'assoc': assoc2sachdr,
          'arrival': arrival2sachdr})

def tables2sachdr(tables):
    """Returns a sac header dictionary, including default values, from
    current table instances.  SAC reference time is, in order of availability,
    origin time (origin.time), first sample time (wfdisc.time). 
    
    """              

    hdr = SACDEFAULT.copy()
    for table, tabfun in KB2SAC.iteritems():
        hdr.update(tabfun(tables.get(table, None)))
        
    return hdr


