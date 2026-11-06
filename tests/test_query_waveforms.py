"""
Tests for the pisces.query.waveforms module.

"""
import pytest
from obspy import UTCDateTime
from sqlalchemy import or_

from pisces.query import availability, filter_waveforms
from pisces.tables.kbcore import Affiliation, Network, Site, Wfdisc


def waveform_query(session):
    """Build the pre-filtered query expected by availability."""
    return filter_waveforms(
        session.query(Wfdisc, Affiliation), net="IU", sta="ANMO", chan="BHZ",
        times=(UTCDateTime(0), UTCDateTime(30)), recordlength=None,
    )


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


def test_query_waveforms_availability_requires_entities(session):
    """availability requires Wfdisc and Affiliation entities."""
    with pytest.raises(ValueError, match="Wfdisc and Affiliation"):
        availability(session.query(Wfdisc))
