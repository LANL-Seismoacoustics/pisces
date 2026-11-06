"""
Tests for the pisces.query.waveforms module.

"""
from datetime import datetime

from obspy import UTCDateTime
from sqlalchemy import or_

from pisces.query import availability, filter_waveforms
from pisces.tables.kbcore import Affiliation, Wfdisc


def test_query_waveforms_filters_codes_and_time(session):
    """Build a waveform query with station, channel, and time filters."""
    starttime = UTCDateTime(2021, 1, 1, 0, 1)
    endtime = UTCDateTime(2021, 1, 1, 0, 2)
    observed = filter_waveforms(
        session.query(Wfdisc), sta="AN*", chan="BH?",
        times=(starttime, endtime), affiliation=None,
    )
    expected = (
        session.query(Wfdisc)
        .where(Wfdisc.sta.like("AN%"))
        .where(Wfdisc.chan.like("BH_"))
        .where(Wfdisc.time.between(starttime.timestamp - 86400, endtime.timestamp))
        .where(Wfdisc.endtime >= starttime.timestamp)
    )
    assert observed.statement.compare(expected.statement)


def test_query_waveforms_filters_multiple_patterns(session):
    """Build a waveform query with comma-separated wildcard patterns."""
    starttime = UTCDateTime(2021, 1, 1)
    endtime = UTCDateTime(2021, 1, 1, 0, 5)
    observed = filter_waveforms(
        session.query(Wfdisc), sta="ANMO,TP*", chan="BHN,BHZ",
        times=(starttime, endtime), affiliation=None,
    )
    expected = (
        session.query(Wfdisc)
        .where(or_(Wfdisc.sta.like("ANMO"), Wfdisc.sta.like("TP%")))
        .where(or_(Wfdisc.chan.like("BHN"), Wfdisc.chan.like("BHZ")))
        .where(Wfdisc.time.between(starttime.timestamp - 86400, endtime.timestamp))
        .where(Wfdisc.endtime >= starttime.timestamp)
    )
    assert observed.statement.compare(expected.statement)


def test_query_waveforms_filters_network_and_affiliation_overlap(session):
    """Build a network query with affiliation and epoch-overlap filters."""
    starttime = UTCDateTime(2021, 1, 1)
    endtime = UTCDateTime(2021, 1, 1, 0, 5)
    observed = filter_waveforms(
        session.query(Wfdisc), net="IU", sta="ANMO", chan="BHZ",
        times=(starttime, endtime), affiliation=Affiliation,
    )
    expected = (
        session.query(Wfdisc)
        .where(Wfdisc.sta.like("ANMO"))
        .where(Wfdisc.chan.like("BHZ"))
        .where(Affiliation.sta == Wfdisc.sta)
        .where(Wfdisc.time <= Affiliation.endtime)
        .where(Wfdisc.endtime >= Affiliation.time)
        .where(Affiliation.net.like("IU"))
        .where(Wfdisc.time.between(starttime.timestamp - 86400, endtime.timestamp))
        .where(Wfdisc.endtime >= starttime.timestamp)
    )
    assert observed.statement.compare(expected.statement)


def test_query_waveforms_disables_recordlength_buffer(session):
    """Build standard overlap filters when recordlength is falsey."""
    starttime = UTCDateTime(2021, 1, 1)
    endtime = UTCDateTime(2021, 1, 1, 0, 5)
    observed = filter_waveforms(
        session.query(Wfdisc), sta="TPNV", chan="BHZ",
        times=(starttime, endtime), recordlength=None, affiliation=None,
    )
    expected = (
        session.query(Wfdisc)
        .where(Wfdisc.sta.like("TPNV"))
        .where(Wfdisc.chan.like("BHZ"))
        .where(Wfdisc.time <= endtime.timestamp)
        .where(Wfdisc.endtime >= starttime.timestamp)
    )
    assert observed.statement.compare(expected.statement)


def add_waveform_data(session):
    """Add small overlapping and gapped waveform records for availability tests."""
    affiliation = Affiliation(net="IU", sta="ANMO", time=0, endtime=100)
    rows = [
        Wfdisc(sta="ANMO", chan="BHZ", time=0, endtime=10, samprate=40,
               wfid=101, lddate=datetime(2020, 1, 1)),
        Wfdisc(sta="ANMO", chan="BHZ", time=10, endtime=20, samprate=40,
               wfid=102, lddate=datetime(2020, 1, 2)),
        Wfdisc(sta="ANMO", chan="BHZ", time=22, endtime=30, samprate=40,
               wfid=103, lddate=datetime(2020, 1, 3)),
        Wfdisc(sta="ANMO", chan="BHZ", time=0, endtime=30, samprate=20,
               wfid=104, lddate=datetime(2020, 1, 4)),
    ]
    session.add_all([affiliation, *rows])
    session.commit()
    return affiliation, rows


def remove_waveform_data(session, affiliation, rows):
    """Remove availability test rows."""
    for row in rows:
        session.delete(row)
    session.delete(affiliation)
    session.commit()


def waveform_query(session):
    """Build the pre-filtered query expected by availability."""
    return filter_waveforms(
        session.query(Wfdisc, Affiliation), net="IU", sta="ANMO", chan="BHZ",
        times=(UTCDateTime(0), UTCDateTime(30)), recordlength=None,
    )


def test_query_waveforms_availability_merges_spans(session):
    """availability merges overlapping and touching spans by sample rate."""
    affiliation, rows = add_waveform_data(session)
    try:
        observed = availability(waveform_query(session))
        assert [(r.network, r.station, r.location, r.channel, r.samplerate,
                 r.earliest, r.latest) for r in observed] == [
            ("IU", "ANMO", "--", "BHZ", 20.0, 0.0, 30.0),
            ("IU", "ANMO", "--", "BHZ", 40.0, 0.0, 20.0),
            ("IU", "ANMO", "--", "BHZ", 40.0, 22.0, 30.0),
        ]
        assert observed[0]._mapping.keys() == observed[0]._fields
    finally:
        remove_waveform_data(session, affiliation, rows)


def test_query_waveforms_availability_merges_gaps(session):
    """availability merges spans separated by the mergegaps tolerance."""
    affiliation, rows = add_waveform_data(session)
    try:
        observed = availability(waveform_query(session), mergegaps=2)
        assert [(r.samplerate, r.earliest, r.latest) for r in observed
                if r.samplerate == 40.0] == [(40.0, 0.0, 30.0)]
    finally:
        remove_waveform_data(session, affiliation, rows)


def test_query_waveforms_availability_merges_sample_rates(session):
    """availability can merge spans from nearby sample rates in Python."""
    affiliation, rows = add_waveform_data(session)
    extra = Wfdisc(sta="ANMO", chan="BHZ", time=20, endtime=35,
                   samprate=39.95, wfid=105, lddate=datetime(2020, 1, 5))
    rows.append(extra)
    session.add(extra)
    session.commit()
    try:
        observed = availability(waveform_query(session), mergesamplerate=0.1)
        assert [(r.samplerate, r.earliest, r.latest) for r in observed] == [
            (20.0, 0.0, 30.0), (40.0, 0.0, 35.0),
        ]
    finally:
        remove_waveform_data(session, affiliation, rows)
