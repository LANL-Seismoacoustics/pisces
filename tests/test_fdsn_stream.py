"""
Tests for pisces.fdsn.stream (Wfdisc row <-> ObsPy Trace).

"""
import os
import tempfile

import numpy as np
import pytest
from obspy import Stream, Trace, UTCDateTime

import pisces.fdsn.stream as trace
from pisces.fdsn.stream import stream, trim_stream, wfdisc2obspyhdr, wfdisc2trace
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


def test_stream_converts_wfdisc_rows():
    """stream converts Wfdisc rows without trimming their traces."""
    data = np.arange(10, dtype='>f4')
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'x.bin')
        with open(path, 'wb') as f:
            data.tofile(f)

        wf = make_wfdisc(
            datatype='t4', dir=d, dfile='x.bin', foff=0,
            time=0.0, endtime=9.0,
        )
        query = type('Query', (), {'__iter__': lambda self: iter([wf])})()

        # stream needs the entity metadata normally supplied by SQLAlchemy.
        query.column_descriptions = [{'entity': Wfdisc}]
        st = stream(query)

    assert len(st) == 1
    assert st[0].stats.starttime == UTCDateTime(0)
    assert st[0].stats.endtime == UTCDateTime(9)


def test_trim_stream_trims_and_checks_coverage():
    """trim_stream trims traces and returns the modified stream."""
    data = np.arange(10, dtype='>f4')
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, 'x.bin')
        with open(path, 'wb') as f:
            data.tofile(f)

        wf = make_wfdisc(datatype='t4', dir=d, dfile='x.bin', foff=0)
        query = type('Query', (), {'__iter__': lambda self: iter([wf])})()
        query.column_descriptions = [{'entity': Wfdisc}]
        st = trim_stream(stream(query), UTCDateTime(2), UTCDateTime(5), tolerance=0)

    assert st[0].stats.starttime == UTCDateTime(2)
    assert st[0].stats.endtime == UTCDateTime(5)


def test_trim_stream_tolerance_failure():
    """trim_stream raises when traces miss the requested interval."""
    st = Stream([Trace(data=np.arange(5))])
    st[0].stats.starttime = UTCDateTime(0)

    with pytest.raises(ValueError, match='outside of tolerance'):
        trim_stream(st, UTCDateTime(2), UTCDateTime(8), tolerance=0.1)


def test_trim_stream_empty_stream():
    """trim_stream leaves an empty stream empty."""
    st = trim_stream(Stream(), UTCDateTime(2), UTCDateTime(8), tolerance=0)

    assert len(st) == 0


def test_stream_wraps_unreadable_waveform_error():
    """stream reports the Wfdisc path when a waveform cannot be read."""
    wf = make_wfdisc(dir='/missing', dfile='waveform', datatype='t4')
    query = type('Query', (), {'__iter__': lambda self: iter([wf])})()
    query.column_descriptions = [{'entity': Wfdisc}]

    with pytest.raises(OSError, match="Can't read /missing/waveform"):
        stream(query)


def test_stream_skips_missing_traces(monkeypatch):
    """stream omits rows whose converter returns no trace."""
    wf = make_wfdisc()
    query = type('Query', (), {'__iter__': lambda self: iter([wf])})()
    query.column_descriptions = [{'entity': Wfdisc}]
    monkeypatch.setattr(trace, 'wfdisc2trace', lambda row: None)

    assert len(stream(query)) == 0


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
