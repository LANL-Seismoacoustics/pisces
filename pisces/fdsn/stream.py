"""
Conversions between KB Core Wfdisc rows and ObsPy Trace objects.

`wfdisc2trace` builds a `Trace` whose `.stats` always reflects the `wfdisc`
row's own column values (station/channel/sample rate/start time/etc.), via
`read_waveform`'s dispatch (`pisces.io.waveforms.WAVEFORM_READERS`).
Every registered waveform reader -- including the ones that read a real
file format internally, like `'sd'` miniSEED or `'sc'` SAC -- returns only a
raw sample array, discarding whatever in-file header ObsPy may have parsed
along the way. So there is no file-reported sub-header
(`.stats.mseed`/`.stats.sac`) to reconcile here: the `wfdisc` row is the
only source of truth for `wfdisc2trace`'s output. Code that wants a file's
original header (not reconciled against any table) should read that file
directly with plain ObsPy instead.

"""
import os

from obspy.core import Stats, Stream, Trace, UTCDateTime

from pisces.io.util import _buildhdr
from pisces.io.waveforms import read_waveform
from pisces.util import _get_entities


def wfdisc2obspyhdr(wf):
    """
    Build an ObsPy Stats instance purely from a Wfdisc row's own column
    values (sta/chan/samprate/nsamp/calib/time) -- no file is read.

    """
    keymap = {'npts': 'nsamp', 'calib': 'calib', 'channel': 'chan',
              'sampling_rate': 'samprate', 'station': 'sta'}
    obshdr = _buildhdr(keymap, wf)
    obshdr['starttime'] = UTCDateTime(float(wf.time))
    obshdr['delta'] = 1. / wf.samprate

    return Stats(header=obshdr)


def wfdisc2trace(wf):
    """
    Takes a fielded wfdisc row record and produces a Trace whose header
    (`.stats`) always reflects the wfdisc row's own values, or None.

    Raises
    ------
    IOError
        Can't read the waveform file.

    """
    hdr = wfdisc2obspyhdr(wf)

    data = read_waveform(os.sep.join([wf.dir, wf.dfile]), wf.datatype, wf.foff,
                         wf.nsamp)

    if data is not None:
        tr = Trace(data=data, header=hdr)
    else:
        tr = None

    return tr


def stream(q):
    """Convert Wfdisc rows to an ObsPy Stream.

    Parameters
    ----------
    q : sqlalchemy.orm.Query
        Query containing a Wfdisc entity.

    Raises
    ------
    OSError
        If a waveform file cannot be read.
    """
    Wfdisc, = _get_entities(q, "Wfdisc")
    traces = []
    for row in q:
        wf = row if isinstance(row, Wfdisc) else getattr(row, Wfdisc.__name__)
        try:
            tr = wfdisc2trace(wf)
        except OSError as exc:
            raise OSError(f"Can't read {wf.dir}/{wf.dfile}.") from exc
        if tr:
            traces.append(tr)

    return Stream(traces)


def trim_stream(st, starttime, endtime, tolerance=None):
    """Trim an ObsPy Stream and optionally validate its time coverage.

    Parameters
    ----------
    st : obspy.Stream
        Stream to trim in place.
    starttime, endtime : obspy.UTCDateTime
        Requested trim interval.
    tolerance : float, optional
        Raise ``ValueError`` if the resulting stream does not cover the
        requested interval within this many seconds.

    Returns
    -------
    obspy.Stream
        The trimmed input stream.
    """
    st.trim(starttime, endtime)
    if all((tolerance, starttime, endtime)) and st:
        min_t = min(tr.stats.starttime for tr in st)
        max_t = max(tr.stats.endtime for tr in st)
        if abs(min_t - starttime) > tolerance or abs(max_t - endtime) > tolerance:
            raise ValueError(f"Trace times are outside of tolerance: {tolerance} seconds")

    return st
