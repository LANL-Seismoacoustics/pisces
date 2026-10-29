"""
Query-building functions for getting waveforms.

Based on the outputs of filter_stations


from obspy import UTCDateTime
from pisces.query import filter_stations, filter_waveforms
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
from typing import Optional

from obspy import UTCDateTime
from sqlalchemy import func, and_, or_, literal
from sqlalchemy.orm import Query

from ..util import _get_entities, make_wildcard_list


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
    """ Request wfdisc rows.

    Parameters
    ----------
    query : sqlalchemy.orm.Query
    net, sta, chan : str
        Network, station, channel code pattern. Supports wildcards: * for any sequence,
        ? for single character, comma-separated for multiple patterns
    times : tuple of (time, endtime) [Wfdisc]
        Anything that obspy.UTCDateTime can consume is accepted.
    recordlength : int (default is one day, 60*60*24=86400)
        Number of seconds of typical wfdisc record length.  Knowing this can help ensure records
        that straddle the end of the request times are properly returned. Set to something
        Falsey to use standard time windowing, like recordlength=None
    clip : str {'c', 'n'}
        Filter on the Wfdisc.clip flag: "c" for clipped, "n" for not clipped.
    affiliation : Affiliaton table class, required if "net is specified
        If the incoming query didn't include the Affiliation table, adding it here _won't_ include
        it in the results.  It's just used for filtering.

    Returns
    -------
    query
        Filtered and joined version of the original query.

    Joins
    -----
    Affiliation.sta == Wfdisc.sta,
    Wfdisc.time <= Affiliation.endtime,
    Wfdisc.endtime >= Affiliation.time,

    """
    Affiliation, Wfdisc = _get_entities(query, "Affiliation", "Wfdisc")
    Affiliation = affiliation or Affiliation # use provided Affiliation

    if net and not Affiliation:
        msg = "Affiliation table required with `net` parameter."
        raise ValueError(msg)

    starttime, endtime = [
        UTCDateTime(t).timestamp if t is not None else None
        for t in times
    ]

    # these lists may be empty
    nets = make_wildcard_list(net)
    stas = make_wildcard_list(sta)
    chans = make_wildcard_list(chan)

    # XXX: need to consider affil.time, affil.endtime for stations
    q = query.session.query(
        Wfdisc
    ).filter(
        or_(*[Wfdisc.sta.like(sta) for sta in stas]),
        or_(*[Wfdisc.chan.like(chan) for chan in chans]),
    ).filter(
        Wfdisc.time <= Affiliation.endtime,
        Wfdisc.endtime >= Affiliation.time,
    )

    if nets:
        q = q.filter(
            Affiliation.sta == Wfdisc.sta,
            or_(*[Affiliation.net.like(net) for net in nets]),
            Wfdisc.time <= Affiliation.endtime,
            Wfdisc.endtime >= Affiliation.time,
        )

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
def availability(query, net, sta, chan, starttime, endtime):
    """ Get the full-resolution contiguous time-series listings.

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

    Returns
    -------
    SQLAlchemy Query that returns result tuples:

    The text format for the query method follows this pattern:
    NET STA LOC CHAN QUAL SAMPRATE EARLIEST LATEST
    NET STA LOC CHAN QUAL SAMPRATE EARLIEST LATEST

    If the show parameter is set to latestupdate, the text format includes an additional column with
    the latest update time:
    NET STA LOC CHAN QUAL SAMPRATE EARLIEST LATEST UPDATED
    NET STA LOC CHAN QUAL SAMPRATE EARLIEST LATEST UPDATED

    If the merge parameter is set to samplerate,quality these respective fields are omitted:
    NET STA LOC CHAN EARLIEST LATEST UPDATED
    NET STA LOC CHAN EARLIEST LATEST UPDATED

    Joins
    -----
    Affiliation.sta == Wfdisc.sta

    """
    session = query.session
    Affiliation, Wfdisc = _get_entities(query, "Affiliation", "Wfdisc")

    nets = make_wildcard_list(net)
    stas = make_wildcard_list(sta)
    chans = make_wildcard_list(chan)

    # XXX: need to consider affil.time, affil.endtime for stations
    query = session.query(
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
    )


    return query



# this is availability/extent
def extent(
    query: Query,
    net: str,
    sta: str,
    chan: str,
    starttime: float,
    endtime: float,
    merge: Optional[str] = None,
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
