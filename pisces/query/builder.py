"""Fluent SQLAlchemy ``select()`` queries for Pisces tables.

``QueryBuilder`` supplies the table setup and valid ordering around the lower-level
``filter_*`` functions. It is an internal convenience API; the filters remain available for
unusual projections or filter-only tables.

Examples
--------
Build an event query without selecting or passing table classes yourself::

    query = (
        QueryBuilder(session, event=Event, origin=Origin, netmag=Netmag)
        .events(region=(west, east, south, north), prefor=True)
        .magnitudes(mw=(4, 6))
    )
    # or, more readable?
    query = (
        QueryBuilder(session, event=Event, origin=Origin, netmag=Netmag)
        .events(
            region=(west, east, south, north), 
            prefor=True,
        )
        .magnitudes(
            mw=(4, 6),
        )
    )
    # Realize the chain with normal SQLAlchemy.
    rows = session.execute(query.statement).all()

Build a station query from networks down through responses. Network and station filters belong
on the initial ``stations`` call; each later fluent method adds the tables its filter needs::

    responses = (
        QueryBuilder(session, network=Network, affiliation=Affiliation, site=Site,
                     sitechan=Sitechan, sensor=Sensor, instrument=Instrument)
        .stations(net="IU", region=(west, east, south, north))
        .channels(chan="BH?")
        .responses()
    )
    rows = session.execute(responses.statement).all()

The underlying SQLAlchemy statement is available for inspection or further composition::

    print(query.statement)
    stmt = query.statement.order_by(Origin.time)
    rows = session.execute(stmt).all()

The fluent API adds tables before applying their filters, so this is valid::

    client.events().arrivals(phase="P", sta="ANMO")

while unsupported domain transitions are absent rather than becoming runtime query errors::

    client.events().responses()  # no such method

Terminal ``catalog()`` and ``inventory()`` methods establish the intended domain API. Their
converters are not implemented yet; until then, execute ``query.statement`` yourself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from .. import catalog
from . import events, stations
from ..util import _get_entities


class QueryBuilder:
    """Create fluent internal query chains backed by a SQLAlchemy session.

    Parameters
    ----------
    session
        SQLAlchemy session associated with the fluent query chain. Realize a chain with
        ``session.execute(query.statement)``.
    tables
        Pisces ORM table classes keyed by lowercase table name, such as ``event=Event`` and
        ``origin=Origin``. The event chain requires those two tables; ``magnitudes`` additionally
        requires ``netmag`` and ``arrivals`` requires ``assoc`` and ``arrival``. The station
        chain starts with ``network`` and ``affiliation``; its optional layers require ``site``,
        ``sitechan``, ``sensor``, and ``instrument`` as applicable.
    """

    def __init__(self, session: Session, **tables):
        self.session = session
        self.tables = tables

    def _table(self, name: str):
        try:
            return self.tables[name]
        except KeyError as exc:
            raise ValueError(f"QueryBuilder requires {name}={name.title()}.") from exc

    def events(
        self,
        *,
        region=None,
        times=None,
        depth=None,
        evid=None,
        orid=None,
        prefor=False,
        auth=None,
        evname=None,
        etype=None,
    ) -> EventQuery:
        """
        Start an Event/Origin query and apply :func:`pisces.events.filter_events`.

        """
        Event = self._table("event")
        Origin = self._table("origin")
        stmt = events.filter_events(
            select(Event, Origin),
            region=region,
            times=times,
            depth=depth,
            evid=evid,
            orid=orid,
            prefor=prefor,
            auth=auth,
            evname=evname,
            etype=etype,
        )
        return EventQuery(self, stmt)

    def stations(
        self,
        *,
        net=None,
        netname=None,
        network_auth=None,
        affiliation_times=None,
        sta=None,
        times=None,
        region=None,
        staname=None,
        refsta=None,
    ) -> StationQuery:
        """Start a Network/Affiliation/Site query.

        Network filters use the names from :func:`pisces.stations.filter_networks`; the ``auth``
        and ``times`` names are disambiguated here as ``network_auth`` and ``affiliation_times``.
        Station filters otherwise match :func:`pisces.stations.filter_stations`.
        """
        Network = self._table("network")
        Affiliation = self._table("affiliation")
        Site = self._table("site")
        stmt = stations.filter_networks(
            select(Network, Affiliation, Site),
            net=net,
            netname=netname,
            auth=network_auth,
            sta=sta,
            times=affiliation_times,
        )
        stmt = stations.filter_stations(
            stmt,
            sta=sta,
            times=times,
            region=region,
            staname=staname,
            refsta=refsta,
        )
        return StationQuery(self, stmt)


@dataclass(frozen=True)
class EventQuery:
    """An immutable Event/Origin query chain.

    Each filter method returns a new chain; branching does not mutate the original::

        base = client.events(region=region)
        magnitudes = base.magnitudes(mb=(3, 4))
        arrivals = base.arrivals(phase="P")
    """

    client: QueryBuilder
    statement: Select

    def __post_init__(self):
        Event, Origin = _get_entities(self.statement, "Event", "Origin")
        if not (Event and Origin):
            raise ValueError("EventQuery statements must include Event and Origin.")

    def magnitudes(self, *, net=None, auth=None, **magnitudes) -> Self:
        """Include Netmag rows and apply :func:`pisces.events.filter_magnitudes`.

        Keyword magnitude ranges match ``filter_magnitudes``: for example,
        ``mw=(4, 6)`` or ``mb=(None, 5)``. Station magnitude filtering (``sta=...``) is not in this
        initial fluent API; use ``filter_magnitudes`` directly when Stamag is needed.

        """
        Netmag = self.client._table("netmag")
        if not _get_entities(self.statement, "Netmag")[0]:
            stmt = self.statement.add_columns(Netmag)
        else:
            stmt = self.statement
        stmt = events.filter_magnitudes(stmt, net=net, auth=auth, **magnitudes)
        return type(self)(self.client, stmt)

    def arrivals(
        self, *, sta=None, auth=None, times=None, orid=None, phase=None
    ) -> Self:
        """
        Include Assoc and Arrival rows and apply :func:`pisces.events.filter_arrivals`.

        """
        Assoc = self.client._table("assoc")
        Arrival = self.client._table("arrival")
        selected_assoc, selected_arrival = _get_entities(self.statement, "Assoc", "Arrival")
        stmt = self.statement
        if not selected_assoc:
            stmt = stmt.add_columns(Assoc)
        if not selected_arrival:
            stmt = stmt.add_columns(Arrival)
        stmt = events.filter_arrivals(
            stmt,
            sta=sta,
            auth=auth,
            times=times,
            orid=orid,
            phase=phase,
        )
        return type(self)(self.client, stmt)

    def catalog(self, **kwargs):
        """Build an ObsPy Catalog from this event query.

        Requires ``pisces.catalog.catalog(session, stmt, **kwargs)``.
        """
        return catalog.catalog(self.client.session, self.statement, **kwargs)


@dataclass(frozen=True)
class StationQuery:
    """An immutable Network/Affiliation/Site query chain."""

    client: QueryBuilder
    statement: Select

    def __post_init__(self):
        Network, Affiliation, Site = _get_entities(
            self.statement, "Network", "Affiliation", "Site"
        )
        if not (Network and Affiliation and Site):
            raise ValueError("StationQuery statements must include Network, Affiliation, and Site.")

    def channels(self, *, sta=None, chan=None, times=None) -> Self:
        """Include Sitechan rows and apply :func:`pisces.stations.filter_stations`."""
        Sitechan = self.client._table("sitechan")
        if _get_entities(self.statement, "Sitechan")[0]:
            stmt = self.statement
        else:
            stmt = self.statement.add_columns(Sitechan)
        stmt = stations.filter_stations(stmt, sta=sta, chan=chan, times=times)
        return type(self)(self.client, stmt)

    def responses(self, *, sta=None, chan=None, times=None) -> Self:
        """Include response rows and apply :func:`pisces.stations.filter_responses`.

        Sitechan is added first because it links the Site chain to Sensor. The returned chain can
        be realized as a response-level inventory with :meth:`inventory`.

        TODO: expose additional response filters here when ``filter_responses`` supports them.
        """
        Sitechan = self.client._table("sitechan")
        Sensor = self.client._table("sensor")
        Instrument = self.client._table("instrument")
        selected_sitechan, selected_sensor, selected_instrument = _get_entities(
            self.statement, "Sitechan", "Sensor", "Instrument"
        )
        stmt = self.statement
        if not selected_sitechan:
            stmt = stmt.add_columns(Sitechan)
        if not selected_sensor:
            stmt = stmt.add_columns(Sensor)
        if not selected_instrument:
            stmt = stmt.add_columns(Instrument)
        stmt = stations.filter_responses(stmt, sta=sta, chan=chan, times=times)
        return type(self)(self.client, stmt)

    def inventory(self):
        """Build an ObsPy Inventory at the deepest layer included in this chain.

        ``stations().inventory()`` is station-level, ``channels().inventory()`` is channel-level,
        and ``responses().inventory()`` is response-level.
        """
        if _get_entities(self.statement, "Instrument")[0]:
            level = "response"
        elif _get_entities(self.statement, "Sitechan")[0]:
            level = "channel"
        else:
            level = "station"

        # TODO: call pisces.inventory.make_inventory(self.statement, level=level) once that
        # converter is implemented; it is currently an unfinished stub.
        raise NotImplementedError(f"{level}-level Inventory construction is not implemented yet.")
