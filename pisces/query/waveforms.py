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
# Availability and extent operate on filtered queries in pisces.fdsn.stream.

Data-header/quality indicators are ``D``, ``R``, ``Q``, and ``M``. ``STATUS`` is
one of ``OPEN``, ``RESTRICTED``, or ``PARTIAL``.

"""

from obspy import UTCDateTime
from sqlalchemy import or_

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
