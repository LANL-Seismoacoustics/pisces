"""
Conversions between ObsPy Trace headers (as read from miniSEED) and KB Core
table rows.

Use this module after reading a miniSEED file with ObsPy when preparing
file-backed waveform records. It extracts waveform and basic network, station,
and channel identity metadata available from the trace header. miniSEED alone
does not provide a complete station or channel record, and callers must
validate or supply database-specific fields before persisting rows.

Mirrors `pisces.io.sac`'s shape: a registry of per-table functions
(`TRACE2TABLES`), each taking an ObsPy `Trace`, and a `trace2tables(trace)`
entry point that calls all (or a selected subset) of them.

Unlike SAC, miniSEED's `Trace.stats` is already the canonical, resolved
header -- there's no separate raw sub-header to translate through (ObsPy's
``Trace.stats.mseed`` only carries record-level details like encoding and
record length, nothing relevant to KB Core tables). So each conversion
function here reads `Trace.stats` fields directly, with no intermediate
object standing in for the file header the way `SACTrace` does for SAC.

Read-only for now; see `misc/io.md` for the planned write-path shape.

"""
from pisces.io.util import Registry

# registry of functions: Trace -> list of table row dicts, keyed by
# canonical table name. Users can add entries from their own code, e.g.:
#   from pisces.io.mseed import TRACE2TABLES
#   @TRACE2TABLES('my_table')
#   def trace2mytable(trace): ...
TRACE2TABLES = Registry()


@TRACE2TABLES('wfdisc')
def trace2wfdisc(trace):
    """Trace -> list of 0 or 1 wfdisc table row dicts.

    wfdisc.datatype is set to 'sd', a pisces convenience (not an actual KB
    Core or CSS 3.0 datatype) that reads miniSEED data directly through
    ObsPy, with no reformatting/copying.

    """
    stats = trace.stats
    row = {
        'sta': stats.station,
        'chan': stats.channel,
        'time': stats.starttime.timestamp,
        'endtime': stats.endtime.timestamp,
        'nsamp': stats.npts,
        'samprate': stats.sampling_rate,
        'calib': stats.get('calib', 1.0),
        'datatype': 'sd',
    }
    return [row]


@TRACE2TABLES('site')
def trace2site(trace):
    """Trace -> list of 0 or 1 site table row dicts."""
    sta = trace.stats.station
    return [{'sta': sta}] if sta else []


@TRACE2TABLES('sitechan')
def trace2sitechan(trace):
    """Trace -> list of 0 or 1 sitechan table row dicts."""
    sta = trace.stats.station
    chan = trace.stats.channel
    if not (sta or chan):
        return []
    return [{'sta': sta, 'chan': chan}]


@TRACE2TABLES('affiliation')
def trace2affiliation(trace):
    """Trace -> list of 0 or 1 affiliation table row dicts."""
    net = trace.stats.network
    sta = trace.stats.station
    if not (net or sta):
        return []
    return [{'net': net, 'sta': sta}]


def trace2tables(trace, tables=None):
    """
    Scrape a miniSEED-sourced ObsPy Trace's header into KB Core table row
    dicts.

    Parameters
    ----------
    trace : obspy.core.trace.Trace
    tables : list of str, optional
        Canonical table names to produce. Default is all of them:
        ['affiliation', 'site', 'sitechan', 'wfdisc']

    Returns
    -------
    dict
        {canonical table name: [row dict, ...]}. Tables with no non-null
        values to offer are omitted.

    Notes
    -----
    Some things must still be checked or filled in before adding rows to a
    database: affiliation.time/endtime; site.ondate; sitechan.ondate/chanid;
    wfdisc.dir/dfile/foff/wfid.

    """
    if tables is None:
        tables = list(TRACE2TABLES)

    out = {}
    for table in tables:
        rows = TRACE2TABLES[table](trace)
        if rows:
            out[table] = rows

    return out
