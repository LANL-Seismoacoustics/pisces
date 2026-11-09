"""
Tests for pisces.fdsn.stream (Wfdisc row <-> ObsPy Trace).

"""
import os
import tempfile

import numpy as np
import pytest
from obspy import Stream, Trace, UTCDateTime
from sqlalchemy import func, literal, or_

import pisces.fdsn.stream as trace
from pisces.fdsn.stream import availability, extent, stream, trim_stream, wfdisc2obspyhdr, wfdisc2trace
from pisces.query import filter_waveforms
from pisces.tables.kbcore import Affiliation, Network, Site, Wfdisc




def waveform_query(session):
    """Build the pre-filtered query expected by availability and extent."""
    return filter_waveforms(
        session.query(Wfdisc, Affiliation), net="IU", sta="ANMO", chan="BHZ",
        times=(UTCDateTime(0), UTCDateTime(30)), recordlength=None,
    )


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


def test_stream_headonly_skips_waveform_file():
    """stream headonly returns a dataless trace from the Wfdisc header."""
    wf = make_wfdisc(dir='/missing', dfile='waveform', datatype='t4')
    query = type('Query', (), {'__iter__': lambda self: iter([wf])})()
    query.column_descriptions = [{'entity': Wfdisc}]

    st = stream(query, headonly=True)

    assert len(st) == 1
    assert st[0].data.size == 0
    assert st[0].stats.station == 'STA'
    assert st[0].stats.npts == 10


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
def test_query_waveforms_availability_merges_spans(session, availability_data):
    """availability merges overlapping and touching spans by sample rate."""
    observed = availability(waveform_query(session))
    assert [(r.network, r.station, r.location, r.channel, r.samplerate,
             r.earliest, r.latest) for r in observed] == [
        ("IU", "ANMO", "--", "BHZ", 20.0, 0.0, 30.0),
        ("IU", "ANMO", "--", "BHZ", 40.0, 0.0, 20.0),
        ("IU", "ANMO", "--", "BHZ", 40.0, 22.0, 30.0),
    ]
    assert observed[0]._mapping.keys() == observed[0]._fields


def test_query_waveforms_availability_merges_gaps(session, availability_data):
    """availability merges spans separated by the mergegaps tolerance."""
    observed = availability(waveform_query(session), mergegaps=2)
    assert [(r.samplerate, r.earliest, r.latest) for r in observed
            if r.samplerate == 40.0] == [(40.0, 0.0, 30.0)]


def test_query_waveforms_availability_merges_sample_rates(session, availability_data):
    """availability can merge spans from nearby sample rates in Python."""
    extra = Wfdisc(sta="ANMO", chan="BHZ", time=20, endtime=35,
                   samprate=39.95, wfid=105)
    session.add(extra)
    session.commit()
    try:
        observed = availability(waveform_query(session), mergesamplerate=0.1)
        assert [(r.samplerate, r.earliest, r.latest) for r in observed] == [
            (20.0, 0.0, 30.0), (40.0, 0.0, 35.0),
        ]
    finally:
        session.delete(extra)
        session.commit()


def test_query_waveforms_availability_shows_latest_update(session, availability_data):
    """availability includes the latest update when requested."""
    observed = availability(waveform_query(session), show="latestupdate")

    assert observed[0].updated.year == 2020
    assert observed[0].updated.day == 4
    assert "updated" in observed[0]._fields


def test_query_waveforms_availability_rejects_invalid_show(session, availability_data):
    """availability rejects unsupported show values."""
    with pytest.raises(ValueError, match="show"):
        availability(waveform_query(session), show="unsupported")


def test_query_waveforms_availability_requires_restriction_substring(
    session, availability_data
):
    """Excluding restricted data requires a restriction substring."""
    with pytest.raises(ValueError, match="restricted_substring"):
        availability(waveform_query(session), includerestricted=False)


def test_query_waveforms_availability_warns_on_unused_restriction_substring(
    session, availability_data
):
    """A restriction substring warns when restricted data is included."""
    with pytest.warns(UserWarning, match="no effect"):
        availability(waveform_query(session), restricted_substring="restricted")


def test_query_waveforms_availability_excludes_restricted_rows(
    session, availability_data
):
    """availability excludes rows matching the restriction substring."""
    query = filter_waveforms(
        session.query(Wfdisc, Affiliation, Site, Network),
        net="IU", sta="ANMO", chan="BHZ",
        times=(UTCDateTime(0), UTCDateTime(30)), recordlength=None,
    )

    observed = availability(
        query,
        includerestricted=False,
        restricted_substring="it is restricted",
    )

    assert observed == []


def test_query_waveforms_availability_includes_restricted_rows(
    session, availability_data
):
    """availability includes restricted rows by default."""
    query = filter_waveforms(
        session.query(Wfdisc, Affiliation, Site, Network),
        net="IU", sta="ANMO", chan="BHZ",
        times=(UTCDateTime(0), UTCDateTime(30)), recordlength=None,
    )

    observed = availability(query, includerestricted=True)

    assert observed


def test_query_waveforms_extent_aggregates_records(session, availability_data):
    """extent builds labeled record-count aggregates by sample rate."""
    query = waveform_query(session)
    observed = extent(query)
    base = query.with_entities(
        Affiliation.net.label("network"), Wfdisc.sta.label("station"),
        Wfdisc.chan.label("channel"), Wfdisc.samprate.label("samplerate"),
        Wfdisc.time.label("earliest"), Wfdisc.endtime.label("latest"),
        Wfdisc.wfid.label("wfid"), Wfdisc.lddate.label("updated"),
    ).filter(Affiliation.sta == Wfdisc.sta).distinct().subquery()
    expected = session.query(
        base.c.network, base.c.station, literal("--").label("location"),
        base.c.channel, base.c.samplerate,
        func.min(base.c.earliest).label("earliest"),
        func.max(base.c.latest).label("latest"),
        func.max(base.c.updated).label("updated"),
        func.count(base.c.wfid).label("timespans"),
        literal("PARTIAL").label("restriction"),
    ).group_by(
        base.c.network, base.c.station, base.c.channel, base.c.samplerate
    ).order_by(
        base.c.network, base.c.station, base.c.channel,
        base.c.samplerate, base.c.earliest
    )
    assert observed.statement.compare(expected.statement)

def test_query_waveforms_extent_requires_restriction_substring(
    session, availability_data
):
    """extent requires a substring when excluding restricted rows."""
    with pytest.raises(ValueError, match="restricted_substring"):
        extent(waveform_query(session), includerestricted=False)


def test_query_waveforms_extent_requires_entities(session):
    """extent requires Wfdisc and Affiliation entities."""
    with pytest.raises(ValueError, match="Wfdisc and Affiliation"):
        extent(session.query(Wfdisc))


def test_query_waveforms_availability_requires_entities(session):
    """availability requires Wfdisc and Affiliation entities."""
    with pytest.raises(ValueError, match="Wfdisc and Affiliation"):
        availability(session.query(Wfdisc))
