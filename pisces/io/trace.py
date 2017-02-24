"""
Conversions between Trace objects and table-like objects.

"""
import os
from obspy.core import UTCDateTime, Trace, Stats
from pisces.io.readwaveform import read_waveform
from pisces.io.util import _buildhdr


def wfdisc2obspyhdr(wf):
    """ ObsPy Stats dict from Wfdisc instance.
    """
    keymap = {'npts': 'nsamp', 'calib': 'calib', 'channel': 'chan',
              'sampling_rate': 'samprate', 'station': 'sta'}
    obshdr = _buildhdr(keymap, wf)
    obshdr['starttime'] = UTCDateTime(float(wf.time))
    obshdr['delta'] = 1./wf.samprate

    return Stats(header=obshdr)


def wfdisc2trace(wf):
    """
    Takes a fielded wfdisc row record and produces a minimal obspy Trace with
    some SAC header fields included, or None.

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
