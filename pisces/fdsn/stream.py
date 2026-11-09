"""
Conversions between KB Core Wfdisc rows and ObsPy Trace objects.

`wfdisc2trace` builds a `Trace` whose `.stats` always reflects the `wfdisc`
row's own column values (station/channel/sample rate/start time/etc.), via
`read_waveform`'s dispatch (`pisces.io.waveforms.WAVEFORM_READERS`).
Every registered waveform reader -- including the ones that read a real
file format internally, like `'sd'` miniSEED or `'sc'` SAC -- returns only a
raw sample array, discarding whatever in-file header ObsPy may have parsed
along the way. So there is no file-reported sub-header
(`.stats.mseed`/`.stats.sac`) to reconcile here: the `wfdisc` row is the
only source of truth for `wfdisc2trace`'s output. Code that wants a file's
original header (not reconciled against any table) should read that file
directly with plain ObsPy instead.

"""
import os
import warnings
from collections import namedtuple

from sqlalchemy import case, func, literal, or_

from obspy.core import Stats, Stream, Trace, UTCDateTime

from pisces.io.util import _buildhdr
from pisces.io.waveforms import read_waveform
from pisces.util import _get_entities



def wfdisc2obspyhdr(wf):
    """
    Build an ObsPy Stats instance purely from a Wfdisc row's own column
    values (sta/chan/samprate/nsamp/calib/time) -- no file is read.

    """
    keymap = {'npts': 'nsamp', 'calib': 'calib', 'channel': 'chan',
              'sampling_rate': 'samprate', 'station': 'sta'}
    obshdr = _buildhdr(keymap, wf)
    obshdr['starttime'] = UTCDateTime(float(wf.time))
    obshdr['delta'] = 1. / wf.samprate

    return Stats(header=obshdr)


def wfdisc2trace(wf):
    """
    Takes a fielded wfdisc row record and produces a Trace whose header
    (`.stats`) always reflects the wfdisc row's own values, or None.

    Raises
    ------
    IOError
        Can't read the waveform file.

    """
    hdr = wfdisc2obspyhdr(wf)

    data = read_waveform(os.sep.join([wf.dir, wf.dfile]), wf.datatype, wf.foff,
                         wf.nsamp)

    if data is not None:
        tr = Trace(data=data, header=hdr)
    else:
        tr = None

    return tr


def stream(q, headonly=False):
    """Convert Wfdisc rows to an ObsPy Stream.

    Parameters
    ----------
    q : sqlalchemy.orm.Query
        Query containing a Wfdisc entity.
    headonly : bool, optional
        If true, return dataless traces built from Wfdisc headers without
        reading waveform files. Default is false.

    Raises
    ------
    OSError
        If a waveform file cannot be read when ``headonly`` is false.
    """
    Wfdisc, = _get_entities(q, "Wfdisc")
    traces = []
    for row in q:
        wf = row if isinstance(row, Wfdisc) else getattr(row, Wfdisc.__name__)
        if headonly:
            tr = Trace(header=wfdisc2obspyhdr(wf))
        else:
            try:
                tr = wfdisc2trace(wf)
            except OSError as exc:
                raise OSError(f"Can't read {wf.dir}/{wf.dfile}.") from exc
        if tr is not None:
            traces.append(tr)

    return Stream(traces)


def trim_stream(st, starttime, endtime, tolerance=None):
    """Trim an ObsPy Stream and optionally validate its time coverage.

    Parameters
    ----------
    st : obspy.Stream
        Stream to trim in place.
    starttime, endtime : obspy.UTCDateTime
        Requested trim interval.
    tolerance : float, optional
        Raise ``ValueError`` if the resulting stream does not cover the
        requested interval within this many seconds.

    Returns
    -------
    obspy.Stream
        The trimmed input stream.
    """
    st.trim(starttime, endtime)
    if all((tolerance, starttime, endtime)) and st:
        min_t = min(tr.stats.starttime for tr in st)
        max_t = max(tr.stats.endtime for tr in st)
        if abs(min_t - starttime) > tolerance or abs(max_t - endtime) > tolerance:
            raise ValueError(f"Trace times are outside of tolerance: {tolerance} seconds")

    return st


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
    if restricted_substring is not None and includerestricted:
        warnings.warn(
            "restricted_substring has no effect when includerestricted=True",
            UserWarning,
        )

    base = _availability_rows(
        query,
        includerestricted=includerestricted,
        restricted_substring=restricted_substring,
    ).subquery()
    partition = [
        base.c.network, base.c.station, base.c.channel, base.c.samplerate
    ]
    ordering = [base.c.earliest, base.c.latest, base.c.wfid]
    previous_latest = func.max(base.c.latest).over(
        partition_by=partition,
        order_by=ordering,
        rows=(None, -1),
    )
    ordered = query.session.query(
        base,
        previous_latest.label("previous_latest"),
    ).subquery()
    starts_span = case(
        (ordered.c.previous_latest.is_(None), 1),
        (ordered.c.earliest > ordered.c.previous_latest + mergegaps, 1),
        else_=0,
    )
    numbered = query.session.query(
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
    numbered = query.session.query(
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
    grouped = query.session.query(*grouped_columns).group_by(
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



def _availability_rows(query, includerestricted=True, restricted_substring=None):
    """Return the filtered, deduplicated Wfdisc rows used by availability APIs."""
    Affiliation, Wfdisc = _get_entities(query, "Affiliation", "Wfdisc")
    Site, Network = _get_entities(query, "Site", "Network")
    if not Affiliation or not Wfdisc:
        raise ValueError("availability query must include Wfdisc and Affiliation")
    if not includerestricted and not restricted_substring:
        raise ValueError(
            "restricted_substring is required when includerestricted=False"
        )
    if not includerestricted and (not Site or not Network):
        raise ValueError(
            "availability query must include Site and Network when excluding restricted data"
        )

    q = query.filter(Affiliation.sta == Wfdisc.sta)
    if Network:
        q = q.filter(Network.net == Affiliation.net)
    if Site:
        q = q.filter(Site.sta == Affiliation.sta)
    if not includerestricted:
        q = q.filter(~or_(
            Site.staname.contains(restricted_substring),
            Network.netname.contains(restricted_substring),
        ))

    return q.with_entities(
        Affiliation.net.label("network"),
        Wfdisc.sta.label("station"),
        Wfdisc.chan.label("channel"),
        Wfdisc.samprate.label("samplerate"),
        Wfdisc.time.label("earliest"),
        Wfdisc.endtime.label("latest"),
        Wfdisc.wfid.label("wfid"),
        Wfdisc.lddate.label("updated"),
    ).distinct()


def extent(query, includerestricted=True, restricted_substring=None):
    """Get earliest/latest extents for the rows represented by ``query``.

    The query must already contain all waveform filters, typically through
    :func:`filter_waveforms`, and include Wfdisc and Affiliation entities.
    Extents are grouped by network, station, channel, and exact sample rate.
    ``timespans`` is the number of contributing Wfdisc records, not merged
    continuous spans. Location is always ``"--"`` and restriction is reported
    as ``"PARTIAL"`` because KB Core does not provide restriction metadata.
    """
    if restricted_substring is not None and includerestricted:
        warnings.warn(
            "restricted_substring has no effect when includerestricted=True",
            UserWarning,
        )
    rows = _availability_rows(
        query, includerestricted=includerestricted,
        restricted_substring=restricted_substring,
    ).subquery()
    return query.session.query(
        rows.c.network,
        rows.c.station,
        literal("--").label("location"),
        rows.c.channel,
        rows.c.samplerate,
        func.min(rows.c.earliest).label("earliest"),
        func.max(rows.c.latest).label("latest"),
        func.max(rows.c.updated).label("updated"),
        func.count(rows.c.wfid).label("timespans"),
        literal("PARTIAL").label("restriction"),
    ).group_by(
        rows.c.network, rows.c.station, rows.c.channel, rows.c.samplerate
    ).order_by(
        rows.c.network, rows.c.station, rows.c.channel,
        rows.c.samplerate, rows.c.earliest
    )
