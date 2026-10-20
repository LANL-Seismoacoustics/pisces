"""
Conversions between KB Core Wfdisc rows and ObsPy Trace objects.

`wfdisc2trace` builds a `Trace` whose `.stats` always reflects the `wfdisc`
row's own column values (station/channel/sample rate/start time/etc.), via
`read_waveform`'s dispatch (`pisces.io.readwaveform.WAVEFORM_READERS`).
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
from obspy.core import UTCDateTime, Trace, Stats
from pisces.io.readwaveform import read_waveform
from pisces.io.util import _buildhdr


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
