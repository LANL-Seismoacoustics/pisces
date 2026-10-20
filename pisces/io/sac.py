"""
Conversions between SAC headers and KB Core table rows.

SAC file reading/parsing itself is left entirely to ObsPy
(:class:`obspy.io.sac.sactrace.SACTrace`, :func:`obspy.read`). This module's
only job is the conversion between a SAC header -- always accessed through
an ObsPy :class:`~obspy.core.trace.Trace`/``.stats.sac`` -- and KB Core
table-row dictionaries, in both directions.

Because ObsPy already resolves SAC's on-disk null sentinels (e.g. -12345,
"-12345  ") to ``None``, none of that sentinel-matching logic is reimplemented
here: a header value is either a real value or ``None``.

The public, format-agnostic entry point is ``trace2tables(trace)``, which
takes a plain ObsPy ``Trace``, matching the rest of the io subpackage.
Internally it converts once to a ``SACTrace`` and passes that to each
registered per-table function (``trace2site``, ``trace2origin``, etc.),
since ``SACTrace``'s attributes are the natural vocabulary for writing
SAC-specific conversion logic (clean attribute names, nulls as ``None``,
enums as strings) -- nicer to write against than raw ``Trace.stats.sac``.
Code that only deals with SAC headers, including user-registered table
functions, is expected to work in terms of ``SACTrace``.

Read-only for now. Write support (``tables2trace`` producing a *new or
updated* ``Trace``/``.stats.sac`` suitable for writing back out with
``SACTrace.write()``) is anticipated but not implemented; see
``misc/io.md`` for the planned shape.

"""
from obspy.core import AttribDict
from obspy.io.sac import SACTrace
import obspy.geodetics as geod

from pisces.io.util import _cast_int, _cast_float, _clean_str, Registry

# registry of functions: SACTrace -> list of table row dicts, keyed by
# canonical table name. Users can add entries from their own code, e.g.:
#   from pisces.io.sac import TRACE2TABLES
#   @TRACE2TABLES('my_table')
#   def trace2mytable(sac): ...
TRACE2TABLES = Registry()

# ievtyp -> etype
ETYPEDICT = {
    'inucl': 'en',
    'ipren': 'ex',
    'ipostn': 'ex',
    'iquake': 'qt',
    'ipreq': 'qt',
    'ipostq': 'qt',
    'ichem': 'ec',
    'iqb': 'me',
    'iqb1': 'me',
    'iqb2': 'me',
    'iqbx': 'me',
    'iqmt': 'mb',
    'ieq': 'qt',
    'ieq1': 'qt',
    'ieq2': 'qt',
    'ime': 'ex',
    'iex': 'ex',
    'inu': 'en',
    'inc': 'mc',
}

# imagsrc -> auth
AUTHDICT = {
    'ineic': 'ISC:NEIC',
    'ipde': 'PDE',
    'iisc': 'ISC',
    'ireb': 'REB-ICD',
    'iusgs': 'IUSGS',
    'ibrk': 'ISC:BERK',
    'icaltech': 'ICALTECH',
    'illnl': 'ILLNL',
    'ievloc': 'IEVLOC',
    'ijsop': 'IJSOP',
    'iuser': 'IUSER',
    'iunknown': 'IUNKNOWN',
}

# imagtyp -> origin magnitude column
MAGTYPEDICT = {
    'imb': 'mb',
    'ims': 'ms',
    'iml': 'ml',
}

# t[0-9]/kt[0-9] pick -> phase name, per SAC2000 convention
PICK2PHASE = {
    't0': 'P',
    't1': 'Pn',
    't2': 'Pg',
    't3': 'S',
    't4': 'Sn',
    't5': 'Sg',
    't6': 'Lg',
    't7': 'LR',
    't8': 'Rg',
    't9': 'pP',
}



def _sac2row(sac, fields, nulls=()):
    """
    Pull `fields` (a {sac_attr: column} map) off a SACTrace into a dict,
    skipping any whose value is None.  `nulls` lists columns to additionally
    drop if their value equals a sentinel (rarely needed; ObsPy already
    resolves SAC nulls to None).

    """
    row = {}
    for attr, col in fields.items():
        val = getattr(sac, attr, None)
        if val is not None:
            row[col] = val
    return row


@TRACE2TABLES('site')
def trace2site(sac):
    """SACTrace -> list of 0 or 1 site table row dicts."""
    row = _sac2row(sac, {'kstnm': 'sta', 'stla': 'lat', 'stlo': 'lon',
                          'stel': 'elev'})
    if 'elev' in row:
        row['elev'] /= 1000.0
    _clean_str(row, ['sta'])
    if row.get('sta'):
        row['sta'] = row['sta'][:6]
    return [row] if row else []


def trace2arraysite(sac):
    """
    Like `trace2site`, but also pulls array deast/dnorth (km) out of SAC's
    user7/user8 fields, per the LANL db2sac/BBFK convention.

    """
    row = _sac2row(sac, {'kstnm': 'sta', 'stla': 'lat', 'stlo': 'lon',
                          'stel': 'elev', 'user7': 'deast', 'user8': 'dnorth'})
    if 'elev' in row:
        row['elev'] /= 1000.0
    _clean_str(row, ['sta'])
    if row.get('sta'):
        row['sta'] = row['sta'][:6]
    return [row] if row else []


@TRACE2TABLES('sitechan')
def trace2sitechan(sac):
    """SACTrace -> list of 0 or 1 sitechan table row dicts."""
    row = _sac2row(sac, {'kstnm': 'sta', 'kcmpnm': 'chan', 'cmpaz': 'hang',
                          'cmpinc': 'vang', 'stdp': 'edepth'})
    if 'edepth' in row:
        row['edepth'] /= 1000.0
    _clean_str(row, ['sta', 'chan'])
    if row.get('sta'):
        row['sta'] = row['sta'][:6]
    return [row] if row else []


@TRACE2TABLES('affiliation')
def trace2affiliation(sac):
    """SACTrace -> list of 0 or 1 affiliation table row dicts."""
    row = _sac2row(sac, {'knetwk': 'net', 'kstnm': 'sta'})
    _clean_str(row, ['net', 'sta'])
    if row.get('sta'):
        row['sta'] = row['sta'][:6]
    return [row] if row else []


@TRACE2TABLES('instrument')
def trace2instrument(sac):
    """SACTrace -> list of 0 or 1 instrument table row dicts."""
    row = _sac2row(sac, {'kinst': 'insname', 'iinst': 'instype'})
    if sac.delta:
        row['samprate'] = int(round(1.0 / sac.delta))
    return [row] if row else []


@TRACE2TABLES('origin')
def trace2origin(sac):
    """
    SACTrace -> list of 0 or 1 origin table row dicts.

    Notes
    -----
    - Origin time/jdate are only filled in if `sac.iztype == 'io'`
      (reference time is an origin time); otherwise origin time is unknown.
    - Magnitude is taken from `sac.mag`/`sac.imagtyp` if present, then
      overridden by `sac.user0`/`sac.kuser0` if `kuser0` names a recognized
      magnitude type (a LANL wfdisc2sac convention).
    - `auth` is taken from `sac.imagsrc`, then overridden by `sac.kuser1` if
      present (also a LANL convention).

    """
    row = _sac2row(sac, {'evla': 'lat', 'evlo': 'lon', 'norid': 'orid',
                          'nevid': 'evid', 'ievreg': 'grn', 'evdp': 'depth'})
    if 'depth' in row:
        row['depth'] /= 1000.0

    if sac.ievtyp in ETYPEDICT:
        row['etype'] = ETYPEDICT[sac.ievtyp]

    if sac.iztype == 'io':
        o = sac.o or 0.0
        origin_time = sac.reftime + o
        row['time'] = origin_time.timestamp
        row['jdate'] = int(origin_time.strftime('%Y%j'))

    if sac.imagtyp in MAGTYPEDICT and sac.mag is not None:
        row[MAGTYPEDICT[sac.imagtyp]] = sac.mag

    # LANL convention: kuser0 names a magnitude type, user0 is its value
    kuser0 = (sac.kuser0 or '').strip()
    if kuser0 in MAGTYPEDICT.values() and sac.user0 is not None:
        row[kuser0] = sac.user0

    if sac.imagsrc in AUTHDICT:
        row['auth'] = AUTHDICT[sac.imagsrc]
    if sac.kuser1:
        row['auth'] = sac.kuser1.strip()

    _cast_float(row, ['lat', 'lon', 'depth'])
    _cast_int(row, ['evid', 'orid'])

    return [row] if row else []


@TRACE2TABLES('event')
def trace2event(sac):
    """SACTrace -> list of 0 or 1 event table row dicts."""
    row = _sac2row(sac, {'nevid': 'evid', 'kevnm': 'evname'})
    _clean_str(row, ['evname'])
    _cast_int(row, ['evid'])
    return [row] if row else []


@TRACE2TABLES('assoc')
def trace2assoc(sac, pickmap=None):
    """
    SACTrace -> list of 0-10 assoc table row dicts, one per filled t[0-9]
    pick header. An alternate t[0-9]->phase mapping can be supplied via
    `pickmap`, overriding entries in `PICK2PHASE`.

    """
    pick2phase = dict(PICK2PHASE)
    if pickmap:
        pick2phase.update(pickmap)

    common = _sac2row(sac, {'az': 'esaz', 'baz': 'seaz', 'gcarc': 'delta'})
    if not common and None not in (sac.stla, sac.stlo, sac.evla, sac.evlo):
        delta = geod.locations2degrees(sac.stla, sac.stlo, sac.evla, sac.evlo)
        _, seaz, esaz = geod.gps2dist_azimuth(sac.stla, sac.stlo, sac.evla, sac.evlo)
        common.update(esaz=esaz, seaz=seaz, delta=delta)

    if sac.kstnm:
        common['sta'] = sac.kstnm.strip()[:6]
    if sac.norid is not None:
        common['orid'] = sac.norid

    rows = []
    for key, default_phase in pick2phase.items():
        pick_time = getattr(sac, key, None)
        if pick_time is None:
            continue
        kkey = 'k' + key
        phase = getattr(sac, kkey, None)
        row = {'phase': (phase.strip() if phase else default_phase)}
        row.update(common)
        rows.append(row)

    return rows


@TRACE2TABLES('arrival')
def trace2arrival(sac, pickmap=None):
    """
    SACTrace -> list of 0-10 arrival table row dicts, one per filled t[0-9]
    pick header. Same phase-naming convention as `trace2assoc`.

    """
    pick2phase = dict(PICK2PHASE)
    if pickmap:
        pick2phase.update(pickmap)

    common = {}
    if sac.kstnm:
        common['sta'] = sac.kstnm.strip()[:6]
    if sac.kcmpnm:
        common['chan'] = sac.kcmpnm.strip()[:8]

    rows = []
    for key, default_phase in pick2phase.items():
        pick_time = getattr(sac, key, None)
        if pick_time is None:
            continue
        kkey = 'k' + key
        phase = getattr(sac, kkey, None)
        itime = sac.reftime + pick_time
        row = {'time': itime.timestamp, 'jdate': int(itime.strftime('%Y%j')),
               'iphase': (phase.strip() if phase else default_phase)}
        row.update(common)
        rows.append(row)

    return rows


@TRACE2TABLES('wfdisc')
def trace2wfdisc(sac):
    """
    SACTrace -> list of 0 or 1 wfdisc table row dicts.

    This is necessarily a skeleton row: the all-important `dir`, `dfile`,
    and `datatype` columns describe the file on disk, not anything in the
    SAC header, and must be filled in by the caller (see `trace.py`).

    """
    if sac.npts is None or not sac.delta:
        return []

    starttime = sac.reftime + (sac.b or 0.0)
    endtime = sac.reftime + (sac.e or 0.0)

    row = {'nsamp': int(sac.npts),
           'time': starttime.timestamp,
           'endtime': endtime.timestamp,
           'jdate': int(starttime.strftime('%Y%j')),
           'samprate': 1.0 / sac.delta}

    if sac.kstnm:
        row['sta'] = sac.kstnm.strip()[:6]
    if sac.kcmpnm:
        row['chan'] = sac.kcmpnm.strip()[:8]
    if sac.scale is not None:
        row['calib'] = float(sac.scale)
    if sac.nwfid is not None:
        row['wfid'] = sac.nwfid

    return [row]


def trace2tables(trace, tables=None):
    """
    Scrape a SAC-sourced ObsPy Trace's header into KB Core table row dicts.

    Parameters
    ----------
    trace : obspy.core.trace.Trace
        Must carry a SAC header, i.e. `trace.stats.sac` exists (as produced
        by `obspy.read(path, format='SAC')`).
    tables : list of str, optional
        Canonical table names to produce. Default is all of them:
        ['affiliation', 'arrival', 'assoc', 'event', 'instrument', 'origin',
        'site', 'sitechan', 'wfdisc']

    Returns
    -------
    dict
        {canonical table name: [row dict, ...]}. Tables with no non-null
        values to offer are omitted.

    Notes
    -----
    Some things must still be checked or filled in before adding rows to a
    database: affiliation.time/endtime; arrival.arid; assoc.orid/arid;
    event.prefor/evid; instrument.inid/dir/dfile/rsptype; site.ondate;
    sitechan.ondate/chanid; wfdisc.dir/dfile/datatype/wfid.

    """
    sac = SACTrace.from_obspy_trace(trace)

    if tables is None:
        tables = list(TRACE2TABLES)

    out = {}
    for table in tables:
        rows = TRACE2TABLES[table](sac)
        if rows:
            out[table] = rows

    return out
