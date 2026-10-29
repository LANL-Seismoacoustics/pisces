"""Tests for the fluent SQLAlchemy ``select()`` query API."""

import pytest
from sqlalchemy import and_, select

from pisces.query.builder import QueryBuilder
from pisces.tables.kbcore import (
    Affiliation,
    Arrival,
    Assoc,
    Event,
    Instrument,
    Netmag,
    Network,
    Origin,
    Sensor,
    Site,
    Sitechan,
)


def client(session):
    return QueryBuilder(
        session,
        event=Event,
        origin=Origin,
        netmag=Netmag,
        assoc=Assoc,
        arrival=Arrival,
        network=Network,
        affiliation=Affiliation,
        site=Site,
        sitechan=Sitechan,
    )


def station_client(session):
    return QueryBuilder(
        session,
        site=Site,
        sitechan=Sitechan,
        network=Network,
        affiliation=Affiliation,
        sensor=Sensor,
        instrument=Instrument,
    )


def test_magnitudes(session):
    """Magnitude chaining adds Netmag and its join, range, and type predicates."""
    observed = (
        client(session)
        .events(region=(-117.0, -115.0, 36.0, 38.0))
        .magnitudes(mb=(5, 5.3))
        .statement
    )
    expected = (
        select(Event, Origin, Netmag)
        .where(Event.evid == Origin.evid)
        .where(Origin.lon.between(-117.0, -115.0))
        .where(Origin.lat.between(36.0, 38.0))
        .where(Netmag.evid == Event.evid)
        .where(Netmag.orid == Origin.orid)
        .where(and_(Netmag.magtype.like("mb"), Netmag.magnitude.between(5, 5.3)))
    )

    assert observed.compare(expected)


def test_arrivals(session):
    """Arrival chaining adds its Assoc/Arrival tables, joins, and filters."""
    observed = (
        client(session)
        .events(evid=[1001])
        .arrivals(phase="P", sta="ANMO")
        .statement
    )
    expected = (
        select(Event, Origin, Assoc, Arrival)
        .where(Event.evid == Origin.evid)
        .where(Origin.evid.in_([1001]))
        .where(Origin.orid == Assoc.orid)
        .where(Arrival.arid == Assoc.arid)
        .where(Assoc.phase.like("P"))
        .where(Assoc.sta.like("ANMO"))
    )

    assert observed.compare(expected)


@pytest.mark.xfail(
    reason="requires catalog(session, stmt, **kwargs); catalog() still accepts legacy Query iterables",
)
def test_catalog(session):
    """Catalog realization accepts the chain's session and Select statement."""
    client(session).events().catalog(description="test")


def test_repeated_magnitudes(session):
    """Repeated magnitude filters keep one Netmag projection while adding predicates."""
    observed = (
        client(session)
        .events()
        .magnitudes(mb=(4, 6))
        .magnitudes(net="GSN")
        .statement
    )
    expected = (
        select(Event, Origin, Netmag)
        .where(Event.evid == Origin.evid)
        .where(Netmag.evid == Event.evid)
        .where(Netmag.orid == Origin.orid)
        .where(and_(Netmag.magtype.like("mb"), Netmag.magnitude.between(4, 6)))
        .where(Netmag.evid == Event.evid)
        .where(Netmag.orid == Origin.orid)
        .where(Netmag.net.like("GSN"))
    )

    assert observed.compare(expected)


def test_stations_and_channels(session):
    """Station chaining composes network, site, and channel filters in order."""
    observed = (
        station_client(session)
        .stations(net="IU", region=(-107.0, -106.0, 34.0, 35.0))
        .channels(chan="BH?")
        .statement
    )
    expected = (
        select(Network, Affiliation, Site, Sitechan)
        .where(Network.net == Affiliation.net)
        .where(Site.sta == Affiliation.sta)
        .where(Network.net.like("IU"))
        .where(Site.sta == Affiliation.sta)
        .where(Site.lon.between(-107.0, -106.0))
        .where(Site.lat.between(34.0, 35.0))
        .where(Site.sta == Sitechan.sta)
        .where(Sitechan.ondate.between(Site.ondate, Site.offdate))
        .where(Site.sta == Affiliation.sta)
        .where(Sitechan.chan.like("BH_"))
    )

    assert observed.compare(expected)


def test_station_inventory(session):
    """A station-only chain infers a station-level Inventory."""
    query = station_client(session).stations()

    with pytest.raises(NotImplementedError, match="station-level"):
        query.inventory()


def test_channel_inventory(session):
    """Adding channels infers a channel-level Inventory."""
    query = station_client(session).stations().channels()

    with pytest.raises(NotImplementedError, match="channel-level"):
        query.inventory()


def test_response_inventory(session):
    """Adding response metadata infers a response-level Inventory."""
    query = station_client(session).stations().responses()

    with pytest.raises(NotImplementedError, match="response-level"):
        query.inventory()
