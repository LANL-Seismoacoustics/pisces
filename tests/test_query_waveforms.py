"""
Tests for the pisces.query.waveforms module.

"""
from obspy import UTCDateTime
from sqlalchemy import or_

from pisces.query import filter_waveforms
from pisces.tables.kbcore import Affiliation, Wfdisc


def test_query_waveforms_filters_codes_and_time(session):
    """Build a waveform query with station, channel, and time filters."""
    starttime = UTCDateTime(2021, 1, 1, 0, 1)
    endtime = UTCDateTime(2021, 1, 1, 0, 2)

    observed = filter_waveforms(
        session.query(Wfdisc),
        sta="AN*",
        chan="BH?",
        times=(starttime, endtime),
        affiliation=None,
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
        session.query(Wfdisc),
        sta="ANMO,TP*",
        chan="BHN,BHZ",
        times=(starttime, endtime),
        affiliation=None,
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
        session.query(Wfdisc),
        net="IU",
        sta="ANMO",
        chan="BHZ",
        times=(starttime, endtime),
        affiliation=Affiliation,
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
        session.query(Wfdisc),
        sta="TPNV",
        chan="BHZ",
        times=(starttime, endtime),
        recordlength=None,
        affiliation=None,
    )
    expected = (
        session.query(Wfdisc)
        .where(Wfdisc.sta.like("TPNV"))
        .where(Wfdisc.chan.like("BHZ"))
        .where(Wfdisc.time <= endtime.timestamp)
        .where(Wfdisc.endtime >= starttime.timestamp)
    )

    assert observed.statement.compare(expected.statement)
