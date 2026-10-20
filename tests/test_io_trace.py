"""
Tests for pisces.io.trace (Wfdisc row <-> ObsPy Trace).

"""
import os
import tempfile

import numpy as np

from pisces.io.trace import wfdisc2obspyhdr, wfdisc2trace
from pisces.tables.kbcore import Wfdisc


def make_wfdisc(**kwargs):
    """Build a Wfdisc row with reasonable defaults, overridable by kwargs."""
    kwargs.setdefault('sta', 'STA')
    kwargs.setdefault('chan', 'BHZ')
    kwargs.setdefault('time', 0.0)
    kwargs.setdefault('nsamp', 10)
    kwargs.setdefault('samprate', 1.0)
    kwargs.setdefault('calib', 2.0)
    return Wfdisc(**kwargs)


def test_wfdisc2obspyhdr_fields():
    """wfdisc2obspyhdr builds a Stats purely from the Wfdisc row's own
    column values (no file is read): sta/chan/samprate/calib/time map to
    their ObsPy Stats equivalents, and delta is derived from samprate.
    """
    wf = make_wfdisc()
    hdr = wfdisc2obspyhdr(wf)

    assert hdr.station == 'STA'
    assert hdr.channel == 'BHZ'
    assert hdr.sampling_rate == 1.0
    assert hdr.delta == 1.0
    assert hdr.calib == 2.0
    assert hdr.starttime.timestamp == 0.0


def test_wfdisc2trace_reads_file_and_uses_wfdisc_header():
    """wfdisc2trace reads wf.nsamp samples from wf.dir/wf.dfile at wf.foff
    using wf.datatype, and the resulting Trace.stats always reflects the
    wfdisc row's own values, not anything from the file itself.
    """
    data = np.arange(10, dtype='>f4')
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'x.bin')
        with open(path, 'wb') as f:
            data.tofile(f)

        wf = make_wfdisc(datatype='t4', dir=d, dfile='x.bin', foff=0)
        tr = wfdisc2trace(wf)

    np.testing.assert_array_equal(tr.data, data)
    assert tr.stats.station == 'STA'
    assert tr.stats.channel == 'BHZ'
    assert tr.stats.calib == 2.0
    assert tr.stats.sampling_rate == 1.0
