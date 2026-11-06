"""
Query-building functions for getting waveforms.

Based on the outputs of filter_stations


from obspy import UTCDateTime
from .stations import filter_stations
from pisces.fdsn import stream

now = UTCDateTime.now().timestamp

query = session.query(Affiliation, Site, Sitechan, Wfdisc)
query = filter_stations(query, net='IU', chan='BH[ENZ]', region=(W, E, S, N))

stquery = filter_waveforms(query, times=(now-86400, None))
st = stream(stquery, tolerance=0.05, headonly=False)

iquery = filter_responses(query, ...)
inv = inventory(iquery, ...)

query = session.query(Event, Origin, Netmag)
query = filter_events(query, region=(W, E, S, N), times=(lastweek, now), depth=(15, None))
query = filter_magnitudes(query, mb=(None, 4.0))
cat = catalog(query, ...)



q = filter_waveforms(...)
a = availability(q, merge=True) # returns an iterator of (sta, loc, chan, UTCDateTime(starttime), UTCDateTime(endtime))
e = extent(q, ...) # returns similar to above, but an actual list of tuples

* “D” or “R” or “Q” or “M” — Data header/quality indicator. Previously, this field was only allowed to be “D”
and was only used to indicate that this is a data header. As of SEED version 2.4 the meaning of this field has been
extended to also indicate the level of quality control that has been applied to the record.
D — The state of quality control of the data is indeterminate.
R — Raw Waveform Data with no Quality Control
Q — Quality Controlled Data, some processes have been applied to the data.
M — Data center modified, time-series values have not been changed.

STATUS is the restricted status, one of: OPEN, RESTRICTED, or PARTIAL

"""

import warnings
from collections import namedtuple

from obspy import UTCDateTime
from sqlalchemy import case, func, literal, or_
from sqlalchemy.orm import Query

from pisces.util import _get_entities

from .util import make_wildcard_list


def filter_waveforms(
    query,
    net=None,
    sta=None,
    chan=None,
    times=None,
    wfid=None,
    recordlength=86400,
    clip=None,
    affiliation=None,
):
    """Request Wfdisc rows.

    Parameters
    ----------
    query : sqlalchemy.orm.Query
        Query whose session is used to build the returned Wfdisc query.
    net, sta, chan : str, optional
        Network, station, and channel patterns. ``*`` and ``?`` wildcards and
        comma-separated patterns are supported. ``net`` requires affiliation.
    times : tuple of (time, endtime)
        Values accepted by :class:`obspy.UTCDateTime`.
    wfid : iterable of int, optional
        Not implemented.
    recordlength : int, optional
        Typical Wfdisc record length in seconds (default: 86400). A falsey
        value disables the record-length buffer.
    clip : {"c", "n"}, optional
        Not implemented; Wfdisc clip flags are not filtered.
    affiliation : mapped table class, optional
        Affiliation table used for network and epoch-overlap filtering.
        Required when ``net`` is specified. Without it, station/channel/time
        filtering still works.

    Returns
    -------
    sqlalchemy.orm.Query
        Query returning filtered Wfdisc rows.

    Notes
    -----
    Location filtering is not supported by this CSS Wfdisc query.
    """
    Affiliation, Wfdisc = _get_entities(query, "Affiliation", "Wfdisc")
    Affiliation = affiliation or Affiliation

    if net and not Affiliation:
        msg = "Affiliation table required with `net` parameter."
        raise ValueError(msg)

    starttime, endtime = [
        UTCDateTime(t).timestamp if t is not None else None
        for t in times
    ]

    nets = make_wildcard_list(net) if net is not None else []
    stas = make_wildcard_list(sta) if sta is not None else []
    chans = make_wildcard_list(chan) if chan is not None else []

    q = query

    if stas:
        q = q.filter(or_(*[Wfdisc.sta.like(pattern) for pattern in stas]))
    if chans:
        q = q.filter(or_(*[Wfdisc.chan.like(pattern) for pattern in chans]))

    if Affiliation:
        q = q.filter(
            Affiliation.sta == Wfdisc.sta,
            Wfdisc.time <= Affiliation.endtime,
            Wfdisc.endtime >= Affiliation.time,
        )

    if nets:
        q = q.filter(or_(*[Affiliation.net.like(pattern) for pattern in nets]))

    if recordlength:
        q = q.filter(
            Wfdisc.time.between(starttime - recordlength, endtime),
            Wfdisc.endtime >= starttime,
        )
    else:
        q = q.filter(
            Wfdisc.time <= endtime,
            Wfdisc.endtime >= starttime,
        )

    return q


# this is like availability/query
def availability(
    query,
    mergegaps=0.0,
    mergesamplerate=None,
    show=None,
    includerestricted=True,
    restricted_substring=None,
):
    """Get availability spans for the rows represented by ``query``.

    The query must already contain all waveform filters, typically through
    :func:`filter_waveforms`, and must include Wfdisc and Affiliation entities.
    Site and Network entities are additionally required when restricted rows
    are excluded. Location is always returned as ``"--"`` because KB Core
    Wfdisc has no location field.

    Parameters
    ----------
    query : sqlalchemy.orm.Query
        Pre-filtered query containing Wfdisc and Affiliation.
    mergegaps : float, optional
        Merge spans separated by no more than this many seconds.
    mergesamplerate : float, optional
        Treat sample rates within this absolute tolerance as equivalent.
    show : {None, "latestupdate"}, optional
        Include ``updated`` with the latest contributing Wfdisc load date.
    includerestricted : bool, optional
        Include restricted rows (default) or exclude them.
    restricted_substring : str, optional
        Substring identifying restricted rows in Site.staname or
        Network.netname. Required when ``includerestricted=False``.

    Returns
    -------
    iterable
        Named result rows with FDSN-style attributes: ``network``,
        ``station``, ``location``, ``channel``, ``samplerate``, ``earliest``,
        and ``latest``; ``updated`` is included when requested.
    """
    if show not in (None, "latestupdate"):
        raise ValueError("show must be None or 'latestupdate'")
    if mergegaps < 0:
        raise ValueError("mergegaps must be non-negative")
    if mergesamplerate is not None and mergesamplerate < 0:
        raise ValueError("mergesamplerate must be non-negative")
    if restricted_substring is not None and includerestricted:
        warnings.warn(
            "restricted_substring has no effect when includerestricted=True",
            UserWarning,
        )
    if not includerestricted and not restricted_substring:
        raise ValueError(
            "restricted_substring is required when includerestricted=False"
        )

    Affiliation, Wfdisc = _get_entities(query, "Affiliation", "Wfdisc")
    Site, Network = _get_entities(query, "Site", "Network")
    if not Affiliation or not Wfdisc:
        raise ValueError("availability query must include Wfdisc and Affiliation")
    if not includerestricted and (not Site or not Network):
        raise ValueError(
            "availability query must include Site and Network when excluding restricted data"
        )

    q = query.filter(Affiliation.sta == Wfdisc.sta)
    if not includerestricted:
        restricted = or_(
            Site.staname.contains(restricted_substring),
            Network.netname.contains(restricted_substring),
        )
        q = q.filter(~restricted)

    base = q.with_entities(
        Affiliation.net.label("network"),
        Wfdisc.sta.label("station"),
        Wfdisc.chan.label("channel"),
        Wfdisc.samprate.label("samplerate"),
        Wfdisc.time.label("earliest"),
        Wfdisc.endtime.label("latest"),
        Wfdisc.wfid.label("wfid"),
        Wfdisc.lddate.label("updated"),
    ).distinct().subquery()
    partition = [
        base.c.network, base.c.station, base.c.channel, base.c.samplerate
    ]
    ordering = [base.c.earliest, base.c.latest, base.c.wfid]
    previous_latest = func.max(base.c.latest).over(
        partition_by=partition,
        order_by=ordering,
        rows=(None, -1),
    )
    ordered = q.session.query(
        base,
        previous_latest.label("previous_latest"),
    ).subquery()
    starts_span = case(
        (ordered.c.previous_latest.is_(None), 1),
        (ordered.c.earliest > ordered.c.previous_latest + mergegaps, 1),
        else_=0,
    )
    numbered = q.session.query(
        ordered,
        starts_span.label("starts_span"),
    ).subquery()
    numbered_partition = [
        numbered.c.network,
        numbered.c.station,
        numbered.c.channel,
        numbered.c.samplerate,
    ]
    numbered_ordering = [
        numbered.c.earliest,
        numbered.c.latest,
        numbered.c.wfid,
    ]
    span_number = func.sum(numbered.c.starts_span).over(
        partition_by=numbered_partition,
        order_by=numbered_ordering,
        rows=(None, 0),
    )
    numbered = q.session.query(
        numbered,
        span_number.label("span_number"),
    ).subquery()
    grouped_columns = [
        numbered.c.network,
        numbered.c.station,
        literal("--").label("location"),
        numbered.c.channel,
        numbered.c.samplerate,
        func.min(numbered.c.earliest).label("earliest"),
        func.max(numbered.c.latest).label("latest"),
    ]
    if show == "latestupdate":
        grouped_columns.append(func.max(numbered.c.updated).label("updated"))
    grouped = q.session.query(*grouped_columns).group_by(
        numbered.c.network,
        numbered.c.station,
        numbered.c.channel,
        numbered.c.samplerate,
        numbered.c.span_number,
    ).order_by(
        numbered.c.network,
        numbered.c.station,
        numbered.c.channel,
        numbered.c.earliest,
        numbered.c.samplerate,
    )

    rows = grouped.all()
    if mergesamplerate is None:
        return rows

    # Exact-rate spans are assembled in SQL. Only the optional rate
    # equivalence pass is materialized in Python.
    fields = ["network", "station", "location", "channel", "samplerate",
              "earliest", "latest"]
    if show == "latestupdate":
        fields.append("updated")
    Result = namedtuple("Availability", fields)
    merged = []
    for row in rows:
        group = next(
            (item for item in merged
             if item.network == row.network
             and item.station == row.station
             and item.channel == row.channel
             and abs(item.samplerate - row.samplerate) <= mergesamplerate),
            None,
        )
        if group is None:
            merged.append(row)
            continue
        previous = group
        if row.earliest <= previous.latest + mergegaps:
            values = [previous.network, previous.station, previous.location,
                      previous.channel, previous.samplerate,
                      min(previous.earliest, row.earliest),
                      max(previous.latest, row.latest)]
            if show == "latestupdate":
                values.append(max(previous.updated, row.updated))
            merged[merged.index(group)] = Result(*values)
        else:
            merged.append(row)

    return merged



# this is availability/extent
def extent(
    query: Query,
    net: str,
    sta: str,
    chan: str,
    starttime: float,
    endtime: float,
    merge: str | None = None,
    includerestricted: bool = True
) -> Query:
    """ Find the earliest and latest time series data available in the wfdisc table.

    Parameters
    ----------
    query : SQLAlchemy query object
        Includes Affiliation, Wfdisc tables
    net, sta, chan : str
        Network, station, channel code pattern. Supports wildcards: * for any sequence,
        ? for single character, comma-separated for multiple patterns
    starttime : float
        Start of time period (in epoch seconds)
    endtime : float
        End of time period (in epoch seconds)
    merge : str {samprate, quality} [not yet implemented]
        Can be multiple values, comma-separated
    includerestricted : bool
        Include (default) or exclude restricted data.

    Returns
    -------
    results : Query
        SQLAlchemy Query that returns result tuples with the following attributes:
        (NET, STA, LOC, CHAN, QUAL, SAMPRATE, EARLIEST, LATEST, UPDATED, SPANCOUNT, STATUS)

    Joins
    -----
    Affiliation.sta == Wfdisc.sta

    """
    # Plan:
        # get affil.net, wfdisc.sta, wfdisc.chan, wfdisc.time, wfdisc.endtime
        # from above subquery, get min(time), max(endtime) for each distinct net, sta, chan
    # TODO: most of this should be in the high-resolution "availability" function, but employed here.
    session = query.session
    Affiliation, Wfdisc = _get_entities(query, "Affiliation", "Wfdisc")

    nets = make_wildcard_list(net)
    stas = make_wildcard_list(sta)
    chans = make_wildcard_list(chan)

    # XXX: need to consider affil.time, affil.endtime for stations
    all_rows = session.query(
        Affiliation.net,
        Wfdisc.sta,
        Wfdisc.chan,
        Wfdisc.time,
        Wfdisc.samprate,
        Wfdisc.endtime,
        Wfdisc.wfid,
        Wfdisc.lddate,
    ).filter(
        Affiliation.sta == Wfdisc.sta,
    ).filter(
        or_(*[Affiliation.net.like(net) for net in nets]),
        or_(*[Wfdisc.sta.like(sta) for sta in stas]),
        or_(*[Wfdisc.chan.like(chan) for chan in chans]),
    ).filter(
        and_(Wfdisc.time <= endtime, Wfdisc.endtime >= starttime)
    ).subquery()

    # select and aggregate from our superset, labeling columns as FDSN extent does
    query = session.query(
        all_rows.c.net.label('network'),
        all_rows.c.sta.label('station'),
        literal("--").label('location'),
        all_rows.c.chan.label('channel'),
        literal("R").label('quality'),
        func.min(all_rows.c.time).label('earliest'),
        func.max(all_rows.c.endtime).label('latest'),
        func.count(all_rows.c.wfid).label('spancount'),
        func.max(all_rows.c.lddate).label('updated'),
        literal("PARTIAL").label('restriction'), #TODO: find a way to actually tell if this is restricted/open/partial
    ).group_by(
        all_rows.c.net, all_rows.c.sta, all_rows.c.chan
    ).order_by(
        all_rows.c.net, all_rows.c.sta, all_rows.c.chan
    )

    return query
