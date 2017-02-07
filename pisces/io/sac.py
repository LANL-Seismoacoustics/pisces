"""
Conversions between SAC header variables and CSS or KB Core fields.


Converts a SAC header dictionary into a list of table dictionaries and vice-versa.

"""
# XXX: currently not working
# TODO: 
#   - remove functions already in pisces.io.trace
#   - make everything just translate dictionaries, not classes and make
#     everything less obspy.Trace-centric
#   - change db.flatfile.KBTABLEDICT to use pisces.schema.util.get_infovals
#   - use pysac (hopefully obspy.io.sac, eventually)
#   - make a bunch of column/header translation functions, like "kcmpnm_to_chan"
#     and "chan_to_kcmpnm", and use them in higher-level functions, like 
#     "sachdr_to_wfdisc" and "wfdisc_to_sachdr".

import sys
import os
from collections import OrderedDict
import functools

from obspy.core import UTCDateTime, AttribDict
import obspy.geodetics as geod

import pisces.tables.kbcore as kb
from pisces.io.readwaveform import read_waveform
from pisces.io.util import _map_header, _buildhdr

# ObsPy default values
OBSPYDEFAULT = {'network': '',
                'station': '',
                'location': '',
                'channel': ''}

# TODO: much of this will be superseded by obspy.io.sac
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

############################# DECORATORS ######################################
# Decorator functions allow readable, reusable handling of header values.
def cast_to_int(original_func):
    """
    Cast a function's argument to int before the function operates on it, like:

    Examples
    --------
    >>> @cast_to_int
    ... def nwfid_to_wfid(nwfid):
    ...     return nwfid
    >>> nwfid_to_wfid(12.3)
    12

    """
    @functools.wraps(original_func)
    def converter(hdr):
        return original_func(int(hdr))
    return converter

def cast_to_float(original_func):
    """
    Cast a function's argument to float before the function operates on it, like:

    Examples
    --------
    >>> @cast_to_float
    ... def stla_to_lat(stla):
    ...     return stla
    >>> lat = stla_to_lat(numpy.float32(12.3))
    >>> type(lat)
    float
    # not numpy.float32

    """
    @functools.wraps(original_func)
    def converter(hdr):
        return original_func(float(hdr))
    return converter

def strip_string(original_func):
    """
    Strip white space from a function's argument to float before the function
    operates on it, like:

    Examples
    --------
    >>> @strip_string
    ... def kcmpnm_to_chan(kcmpnm):
    ...     return kcmpnm[:6]
    >>> kclmpnm_to_chan(' my_too_long_component ')
    'my_too'

    """
    @functools.wraps(original_func)
    def converter(hdr):
        return original_func(int(hdr))
    return converter

def truncate_string(N):
    def make_func(original_func):
        @functools.wraps(original_func)
        def func_wrapper(val):
            return val[:N]
        return func_wrapper


# decorator for when you find default/null SAC header values
# if a value is detected, function returns return_value instead of being executed
# XXX: not clear how this could be used with other decorators
def swap_if_value(detected_value, return_value):
    def check_value(original_func):
        def func_wrapper(arg):
            if arg == detected_value:
                out = return_value
            else:
                out = arg
            return out
        return func_wrapper


# ############################## STRING HEADER CONVERSIONS ####################
# SAC -> CSS
def kcmpnm_to_chan(kcmpnm):
    return kcmpnm.strip()[:8]

def kevnm_to_evname(kevnm):
    return kevnm.strip()

def kinst_to_insname(kinst):
    return kinst.strip()

def knetwk_to_net(knetwk):
    return knetwk.strip()[:8]

def kstnm_to_sta(kstnm):
    return kstnm.strip()[:6]


# CSS -> SAC
def chan_to_kcmpnm(chan):
    return chan

def evname_to_kevnm(evname):
    return evname

def insname_to_kinst(insname):
    return insname

def net_to_knetwk(net):
    return net

def sta_to_kstnm(sta):
    return kstnm


# ############################## INT HEADER CONVERSIONS #######################
# DATA
#
ENUM_NAMES = {1: 'itime', 2: 'irlim', 3: 'iamph', 4: 'ixy', 5: 'iunkn',
              6: 'idisp', 7: 'ivel', 8: 'iacc', 9: 'ib', 10: 'iday', 11: 'io',
              12: 'ia', 13: 'it0', 14: 'it1', 15: 'it2', 16: 'it3', 17: 'it4',
              18: 'it5', 19: 'it6', 20: 'it7', 21: 'it8', 22: 'it9',
              23: 'iradnv', 24: 'itannv', 25: 'iradev', 26: 'itanev',
              27: 'inorth', 28: 'ieast', 29: 'ihorza', 30: 'idown', 31: 'iup',
              32: 'illlbb', 33: 'iwwsn1', 34: 'iwwsn2', 35: 'ihglp', 36: 'isro',
              37: 'inucl', 38: 'ipren', 39: 'ipostn', 40: 'iquake', 41: 'ipreq',
              42: 'ipostq', 43: 'ichem', 44: 'iother', 45: 'igood', 46: 'iglch',
              47: 'idrop', 48: 'ilowsn', 49: 'irldta', 50: 'ivolts', 52: 'imb',
              53: 'ims', 54: 'iml', 55: 'imw', 56: 'imd', 57: 'imx', 58: 'ineic',
              59: 'ipdeq', 60: 'ipdew', 61: 'ipde', 62: 'iisc', 63: 'ireb',
              64: 'iusgs', 65: 'ibrk', 66: 'icaltech', 67: 'illnl', 68: 'ievloc',
              69: 'ijsop', 70: 'iuser', 71: 'iunknown', 72: 'iqb', 73: 'iqb1',
              74: 'iqb2', 75: 'iqbx', 76: 'iqmt', 77: 'ieq', 78: 'ieq1',
              79: 'ieq2', 80: 'ime', 81: 'iex', 82: 'inu', 83: 'inc', 84: 'io_',
              85: 'il', 86: 'ir', 87: 'it', 88: 'iu', 89: 'ieq3', 90: 'ieq0',
              91: 'iex0', 92: 'iqc', 93: 'iqb0', 94: 'igey', 95: 'ilit',
              96: 'imet', 97: 'iodor', 103: 'ios'} 

# ievtyp -> etype
ETYPEDICT = {37: 'en', 38: 'ex', 39: 'ex', 40: 'qt', 41: 'qt', 42: 'qt',
             43: 'ec', 72: 'me', 73: 'me', 74: 'me', 75: 'me', 76: 'mb',
             77: 'qt', 78: 'qt', 79: 'qt', 80: 'ex', 81: 'ex', 82: 'en',
             83: 'mc'}

# evtype -> ievtyp
IEVTYPDICT = dict((_val,_key) for _key,_val in ETYPEDICT.iteritems())
#
# imagsrc -> auth
AUTHDICT = {58: 'ISC:NEIC', 61: 'PDE', 62: 'ISC', 63: 'REB-ICD',
            64: 'IUSGS', 65: 'ISC:BERK', 66: 'ICALTECH', 67: 'ILLNL',
            68: 'IEVLOC', 69: 'IJSOP', 70: 'IUSER', 71: 'IUNKNOWN'}
#
# auth -> imagsrc
IMAGSRCDICT = dict((_val,_key) for _key,_val in AUTHDICT.iteritems())


# SAC -> CSS
def ievreg_to_grn(ievreg):
    return int(ievreg)

def ievtyp_to_etype(ievtyp):
    """Provide the ievtyp(e) integer, get the etype string."""
    return ETYPEDICT[ievtyp]




# the following functions accept a SAC header dictionary, and return respective
# kbcore table instances, assumes default SAC header values set to None
def get_sac_reftime(header):
    """
    Get SAC header reference time as a UTCDateTime instance from a SAC header
    dictionary.

    If using ObsPy to read the SAC file, use debug_headers=True to get the full
    header, including nz time headers.

    """
    # "nz" fields are not kept when ObsPy reads a SAC file.  They're used
    # to make "starttime", then discarded.
    # t0 = nzyear + nzjday + nzhour + nzminute + nzsecond + nzmsec*1000
    # tr.stats.starttime = t0 + b
    # therefore: t0 = starttime - b

    # TODO: let null nz values be 0?
    try:
        yr = header['nzyear']
        if 0 <= yr <= 99:
            yr += 1900
        nzjday = header['nzjday']
        nzhour = header['nzhour']
        nzmin = header['nzmin']
        nzsec = header['nzsec']
        nzmsec = header['nzmsec']
    except KeyError as e:
        msg = "Not enough time information: {}".format(e.message)
        raise KeyError(msg)

    try:
        reftime = UTCDateTime(year=yr, julday=nzjday, hour=nzhour, minute=nzmin,
                              second=nzsec, microsecond=nzmsec * 1000)
        #reftime = datetime.datetime(yr, 1, 1, nzhour, nzmin, nzsec, nzmsec * 1000) + \
        #                            datetime.timedelta(int(nzjday-1))
        # NOTE: epoch seconds can be got by:
        # (reftime - datetime.datetime(1970,1,1)).total_seconds()
    except ValueError, TypeError:
        # may contain -12345 null values?
        msg = "Invalid or missing time headers."
        raise ValueError(msg)

    return reftime

def _cast_int(d, keys):
    for key in keys:
        try:
            d[key] = int(d[key])
        except (TypeError, KeyError):
            # no key, or int(None)
            pass

    return d

def _cast_float(d, keys):
    for key in keys:
        try:
            d[key] = float(d[key])
        except (TypeError, KeyError):
            # no key, or int(None)
            pass

    return d

def _clean_str(d, keys):
    for key in keys:
        try:
            d[key] = d[key].strip()
        except (KeyError, AttributeError):
            # no key, None.strip()
            pass

    return d

def sachdr2site(header):
    """
    Provide a SAC header dictionary, get a site table dictionary.

    """
    sac_site = [('kstnm', 'sta'),
                ('stla', 'lat'),
                ('stlo', 'lon'),
                ('stel', 'elev')]

    sitedict = {}
    for hdr, col in sac_site:
        val = header.get(hdr, None)
        sitedict[col] = val if val != SACDEFAULT[hdr] else None

    # clean up
    try:
        sitedict['elev'] /= 1000.0
    except (TypeError, KeyError):
        #no 'elev'
        pass

    sitedict = _cast_float(sitedict, ['lat', 'lon', 'elev'])
    sitedict = _clean_str(sitedict, ['sta'])

    sitedict['sta'] = sitedict['sta'].strip()[:6]

    return [sitedict] or []


def sachdr2arraysite(header):
    """
    Provide a SAC header dictionary, get a site table dictionary.
    This is a slight modification of sachdr2site that handles deast
    & dnorth being in SAC's user7 & user8 header fields (a poor
    but documented standard that is the de facto appoach
    - see SAC's BBFK or ARRAYMAP or BRTT's db2sac in Antelope).

    Note that user7 & user8 are expected to be in km (consistent
    with SAC expectations).

    """
    sac_site = [('kstnm', 'sta'),
                ('stla', 'lat'),
                ('stlo', 'lon'),
                ('stel', 'elev'),
                ('user7','deast'),
                ('user8','dnorth')]

    sitedict = {}
    for hdr, col in sac_site:
        val = header.get(hdr, None)
        sitedict[col] = val if val != SACDEFAULT[hdr] else None

    # clean up
    try:
        sitedict['elev'] /= 1000.0
    except (TypeError, KeyError):
        #no 'elev'
        pass

    sitedict = _cast_float(sitedict, ['lat', 'lon', 'elev', 'deast', 'dnorth'])
    sitedict = _clean_str(sitedict, ['sta'])

    sitedict['sta'] = sitedict['sta'].strip()[:6]

    return [sitedict] or []


def sachdr2sitechan(header):
    """
    Provide a sac header dictionary, get a sitechan table dictionary.

    """
    sac_sitechan = [('kstnm', 'sta'),
                    ('kcmpnm', 'chan'),
                    ('cmpaz', 'hang'),
                    ('cmpinc', 'vang'),
                    ('stdp', 'edepth')]

    sitechandict = AttribDict()
    for hdr, col in sac_sitechan:
        val = header.get(hdr, None)
        sitechandict[col] = val if val != SACDEFAULT[hdr] else None

    try:
        sitechandict['edepth'] /= 1000.0
    except (TypeError, KeyError):
        #edepth is None or missing
        pass

    sitechandict = _cast_float(sitechandict, ['hang', 'vang', 'edepth'])
    sitechandict = _clean_str(sitechandict, ['sta', 'chan'])
    sitechandict['sta'] = sitechandict['sta'].strip()[:6]

    return [sitechandict] or []

def sachdr2affiliation(header):
    sac_affil = [('knetwk', 'net'),
                 ('kstnm', 'sta')]

    affildict = AttribDict()
    for hdr, col in sac_affil:
        val = header.get(hdr, None)
        affildict[col] = val if val != SACDEFAULT[hdr] else None

    affildict = _clean_str(affildict, ['net', 'sta'])

    affildict['sta'] = affildict['sta'].strip()[:6]

    return [affildict] or []


def sachdr2instrument(header):
    #TODO: investigate hdr['resp0-9'] values
    sac_instr = [('kinst', 'insname'),
                 ('iinst', 'instype'),
                 ('delta', 'samprate')]

    instrdict = AttribDict()
    for hdr, col in sac_instr:
        val = header.get(hdr, None)
        instrdict[col] = val if val != SACDEFAULT[hdr] else None

    # clean up
    try:
        instrdict['samprate'] = int(round(1.0 / instrdict['samprate'],0))
    except (TypeError, KeyError):
        pass

    return [instrdict] or []


def sachdr2origin(header):
    """
    Provide a sac header dictionary, get a filled origin table dictionary.
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
    sac_origin = [('evla', 'lat'),
                  ('evlo', 'lon'),
                  ('norid', 'orid'),
                  ('nevid', 'evid'),
                  ('ievreg', 'grn'),
                  ('evdp', 'depth')]

    origindict = AttribDict()
    for hdr, col in sac_origin:
        val = header.get(hdr, None)
        origindict[col] = val if val != SACDEFAULT[hdr] else None

    #depth
    try:
        origindict['depth'] /= 1000.0
    except (TypeError, KeyError):
        #evdp is None or mising
        pass

    #etype translations
    edict = {37: 'en', 38: 'ex', 39: 'ex', 40: 'qt', 41: 'qt', 42: 'qt',
            43: 'ec', 72: 'me', 73: 'me', 74: 'me', 75: 'me', 76: 'mb',
            77: 'qt', 78: 'qt', 79: 'qt', 80: 'ex', 81: 'ex', 82: 'en',
            83: 'mc'}
    try:
        origindict['etype'] = edict[header['ievtype']]
    except (TypeError, KeyError):
        #ievtyp is None, or not a key in edict
        pass

    #1:
    try:
        t = get_sac_reftime(header)
        if header['iztype'] == 11:
            #reference time is an origin time
            o = header.get('o', None)
            o = o if (o != SACDEFAULT['o']) else 0.0

            origindict['time'] = t.timestamp - o
            origindict['jdate'] = int((t-o).strftime('%Y%j'))
    except (ValueError, KeyError):
        # no trace.stats.sac, no iztype
        pass

    #2: magnitude
    magdict = {52: 'mb', 53: 'ms', 54: 'ml'}
    try:
        origindict[magdict[header['imagtyp']]] = header['mag']
    except (ValueError, KeyError):
        #imagtyp is None or not a key in magdict
        pass

    # is kuser0 is a recognized magnitude type, overwrite mag
    #XXX: this is a LANL wfdisc2sac thing
    try:
        magtype = header['kuser0'].strip()
        if magtype in magdict.values():
            origindict[magtype] = header['user0']
    except (KeyError, ValueError):
        #kuser0 is None
        pass

    #3: origin author
    authdict = {58: 'ISC:NEIC', 61: 'PDE', 62: 'ISC', 63: 'REB-ICD',
            64: 'IUSGS', 65: 'ISC:BERK', 66: 'ICALTECH', 67: 'ILLNL',
            68: 'IEVLOC', 69: 'IJSOP', 70: 'IUSER', 71: 'IUNKNOWN'}
    try:
        origindict['auth'] = authdict[header['imagsrc']]
    except (KeyError, ValueError):
        # imagsrc not in authdict (i.e. sac default value)
        pass

    #XXX: this is LANL wfdisc2sac thing.  maybe turn it off?
    if header.get('kuser1'):
        origindict['auth'] = header['kuser1']

    origindict = _cast_float(origindict, ['lat', 'lon', 'depth'])
    origindict = _cast_int(origindict, ['evid', 'orid'])

    return [origindict] or []


def sachdr2event(header):
    sac_event = [('nevid', 'evid'),
                 ('kevnm', 'evname')]

    eventdict = AttribDict()
    for hdr, col in sac_event:
        val = header.get(hdr, None)
        eventdict[col] = val if val != SACDEFAULT[hdr] else None

    eventdict = _cast_int(eventdict, ['evid'])

    return [eventdict] or []


def sachdr2assoc(header, pickmap=None):
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
    sac_assoc = [('az', 'esaz'),
                 ('baz', 'seaz'),
                 ('gcarc', 'delta')]

    assocdict = AttribDict()
    for hdr, col in sac_assoc:
        val = header.get(hdr, None)
        assocdict[col] = val if val != SACDEFAULT[hdr] else None

    #overwrite if any are None
    if not assocdict:
        try:
            delta = geod.locations2degrees(header['stla'], header['stlo'],
                                           header['evla'], header['evlo'])
            m, seaz, esaz = geod.gps2DistAzimuth(header['stla'], header['stlo'],
                                                 header['evla'], header['evlo'])
            assocdict['esaz'] = esaz
            assocdict['seaz'] = seaz
            assocdict['delta'] = delta
        except (ValueError, TypeError):
            #some sac header values are None
            pass

    if header.get('kstnm', None):
        assocdict['sta'] = header['kstnm']

    orid = header.get('norid', None)
    assocdict['orid'] = orid if orid != SACDEFAULT['norid'] else None

    #now, do the phase arrival mappings
    #for each pick in hdr, make a separate dictionary containing assocdict plus
    #the new phase info.
    assocs = []
    for key in pick2phase:
        kkey = 'k' + key
        #if there's a value in t[0-9]
        if header.get(key, None) not in (SACDEFAULT[key], None):
            #if the phase name kt[0-9] is null
            if header[kkey] == SACDEFAULT[kkey]:
                #take it from the map
                iassoc = {'phase': pick2phase[key]}
            else:
                #take it directly
                iassoc = {'phase': header[kkey]}

            iassoc.update(assocdict)
            assocs.append(iassoc)

    return assocs


def sachdr2arrival(header, pickmap=None):
    """Similar to sachdr2assoc, but produces a list of up to 10 Arrival
    dictionaries.  Same header->phase mapping applies, unless otherwise stated.

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
    arrivaldict = AttribDict()
    if header.get('kstnm', None) not in (SACDEFAULT['kstnm'], None):
        arrivaldict['sta'] = header['kstnm']
    if header.get('kcmpnm', None) not in (SACDEFAULT['kcmpnm'], None):
        arrivaldict['chan'] = header['kcmpnm']

    #phases and arrival times
    t0 = get_sac_reftime(header)
    arrivals = []
    for key in pick2phase:
        kkey = 'k' + key
        # if there's a value in t[0-9]
        if header.get('key', None) not in (SACDEFAULT[key], None):
            itime = t + header[key]
            iarrival = {'time': itime.timestamp,
                        'jdate': int(itime.strftime('%Y%j'))}
            #if the phase name kt[0-9] is null
            if header[kkey] == SACDEFAULT[kkey]:
                #take it from the pick2phase map
                iarrival['iphase'] = pick2phase[key]
            else:
                #take it directly
                iarrival['iphase'] = header[kkey]

            iarrival.update(arrivaldict)
            arrivals.append(iassoc)

    return arrivals


def sachdr2wfdisc(header):
    """Produce wfdisc kbcore table instance from sac header dictionary.
    Clearly this will be a skeleton instance, as the all-important 'dir' and
    'dfile' and 'datatype' must be filled in later.

    """
    t0 = get_sac_reftime(header)
    b = header.get('b', None)
    b = b if (b != SACDEFAULT['b']) else 0.0
    starttime = t0 + b
    e = header.get('e', None)
    e = e if (e != SACDEFAULT['e']) else 0.0
    endtime = t0 + e

    wfdict = AttribDict()
    wfdict['nsamp'] = int(header.get('npts', None))
    wfdict['time'] = starttime.timestamp
    wfdict['endtime'] = endtime.timestamp
    wfdict['jdate'] = int(starttime.strftime('%Y%j'))
    
    wfdict['samprate'] = int(round(1.0 / header['delta']))
    
    kstnm = header.get('kstnm', None)
    if kstnm not in (SACDEFAULT['kstnm'], None):
        wfdict['sta'] = kstnm.strip()[:6]

    kcmpnm = header.get('kcmpnm', None)
    if kcmpnm not in (SACDEFAULT['kcmpnm'], None):
        wfdict['chan'] = kcmpnm.strip()[:8]

    scale = header.get('scale', None)
    if scale not in (SACDEFAULT['scale'], None):
        wfdict['calib'] = float(scale)

    nwfid = header.get('nwfid', None)
    if nwfid not in (SACDEFAULT['nwfid'], None):
        wfdict['wfid'] = nwfid

    wfdict['foff'] = 632

    if sys.byteorder == 'little':
        wfdict['datatype'] = 'f4'
    else:
        wfdict['datatype'] = 't4'

    return [wfdict] or []


def sachdr2tables(header, tables=None):
    """
    Scrape SAC header dictionary into database table dictionaries.

    Parameters
    ----------
    header : dict
        SAC header
    tables : list/tuple of strings, optional
        Table name strings to return.
        Default, ['affiliation', 'arrival', 'assoc', 'event', 'instrument',
        'origin', 'site', 'sitechan', 'wfdisc']

    Returns
    -------
    dict
        Dictionary of lists of table dictionaries.  If only default
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
    fns = {'affiliation': sachdr2affiliation,
           'arrival': sachdr2arrival,
           'assoc': sachdr2assoc,
           'event': sachdr2event,
           'instrument': sachdr2instrument,
           'origin': sachdr2origin,
           'site': sachdr2site,
           'sitechan': sachdr2sitechan,
           'wfdisc': sachdr2wfdisc}

    if tables is None:
        tables = fns.keys()

#     for key in header:
#         if key.startswith('k'):
#             try:
#                 header[key] = header[key].strip()[:6]

    #t = AttribDict()
    t = {}
    for table in tables:
        try:
            itab = fns[table](header)
        except KeyError:
            itab = []

        if itab:
            t[table] = itab

    # t[table] doesn't exist if table's function didn't return anything

    return t


#----------------- CONVERT TABLES TO SAC HEADER DICTIONARY ---------------#
#TODO: make these functions able to gracefully handle None values as inputs
def site2sachdr(s):
    """
    Accepts a fielded site table row and returns a dictionary of corresponding
    sac header field/value pairs.

    June 13, 2016 - added deast/dnorth output to SAC user7/8 header fields
    """
    keymap = {'stel': 'elev', 'stal': 'lat', 'stlo': 'lon',
        'user7': 'deast', 'user8': 'dnorth'}
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
