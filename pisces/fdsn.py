# -*- coding: utf-8 -*-
"""
Pisces Client mirrors the ObsPy FDSN Client interface.

"""
from functools import cached_property
import logging
import os
import warnings

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from obspy import Stream, UTCDateTime
from obspy.core.event.header import EventType

from pisces import events
import pisces.request as req
from pisces import util
from .catalog import KBCORE_EVENT_TYPE, catalog

log = logging.getLogger(__name__)

# client = DBClient(session_or_config_or_URI, **tables)
# get network-level info for stations containing BH? in a region.
# returns joined sitechan, site, affil, and network
# q = client.stations(region=[W, E, S, N], channels='BH?').networks(pref_nets=('II','IU','ISC'))
# get responses for all BH? stations in II
# q = client.networks(networks=['II']).stations(channels='BH?').responses()
# q = client.events(region=[W, E, S, N], prefor=True).magnitudes(mb=(3, 4)).arrivals(phase='P,S', auth='LANL*')
# res = q.all()


def _None_if_none(*values):
    return None if all([val is None for val in values]) else values


def origins_to_fdsntext(origins, header=False):
    """Convert a SQLAlchemy Origin instances to FDSN event text.

    #EventID | Time | Latitude | Longitude | Depth/km | Author | Catalog | Contributor | ContributorID | MagType | Magnitude | MagAuthor | EventLocationName
    #origin.orid|origin.time|origin.lat|origin.lon|origin.depth|netmag.auth|netmag.auth|netmag.auth|netmag.magtype|netmag.magnitude|sregion.srname or event.evname
    #origin.orid|origin.time|origin.lat|origin.lon|origin.depth|origin.auth|origin.auth|origin.auth|('ml','ms','mb')|origin.('ml','ms','mb')|sregion.srname or event.evname
    header_string = '#EventID|Time|Latitude|Longitude|Depth/km|Author|Catalog|Contributor|ContributorID|MagType|Magnitude|MagAuthor|EventLocationName'

    """
    header_string = "EventID | Time | Latitude | Longitude | Depth/km | Author | Catalog | Contributor | ContributorID | MagType | Magnitude | MagAuthor | EventLocationName"
    # this needs to get MagType in there
    origin_columns = (
        "orid",
        "time",
        "lat",
        "lon",
        "depth",
        "auth",
        "auth",
        "auth",
        "orid",
        "mb",
        "mb",
        "auth",
        "grn",
    )
    rows = [
        "|".join(str(getattr(origin, column, "-")) for column in origin_columns)
        for origin in origins
    ]

    if header:
        out = [header_string] + rows
    else:
        out = rows

    return os.linesep.join(out)


class Client(object):
    """
    Basic database request client.

    """

    def __init__(self, dburl_or_session, **tables):
        """
        FDSN-style client interface to a SQL database using a CSS3.0-style schema.

        Parameters
        ----------
        dburl_or_session : str or sqlalchemy.orm.Session instance
            RFC-1738-complient database URL string of the form:
            '<backend>://[<user>[:<password>]@]<server>:<port>/<instance>'
            or a pre-configured SQLAlchemy Session instance
        tables : one or more str or Pisces table class

        Examples
        --------
        >>> client = Client('sqlite:///local/path/to/mydb.sqlite')
        >>> client = Client('sqlite:////full/path/to/mydb.sqlite', site='mysite')
        >>> client = Client('oracle://scott:tiger@dbserver.somewhere.com:8080/mydb')
        >>> client = Client(session)

        >>> from myschema import Origin, Site
        >>> client = Client(session, origin=Origin, site=Site)

        >>> from pisces import crud
        >>> tables = crud.make_tables('origin', 'site', owner='global')
        >>> client = Client(session, **tables)

        """
        if isinstance(dburl_or_session, str):
            engine = sa.create_engine(dburl_or_session)
            session = Session(engine)
        else:
            session = dburl_or_session

        # this is just a test, will fail early if the connection is misconfigured
        # session.bind.connect();

        self.session = session
        self.tables = tables

    def __repr__(self):
        repr_str = "<Client({!r})>"

        return repr_str.format(self.session.bind.url)

    @cached_property # >= py3.8
    def contributors(self):
        """ Sorted list of distinct origin authors (Origin.auth) """
        Origin = self.tables['origin']
        return self.session.query(Origin.auth).distinct().order_by(Origin.auth).all()

    @cached_property # >= py3.8
    def magnitude_types(self):
        """ Sorted list of distinct Netmag.magtype """
        Netmag = self.tables['netmag']
        return self.session.query(Netmag.magtype).distinct().order_by(Netmag.magtype).all()

    def get_events(
        self,
        starttime: UTCDateTime = None,
        endtime: UTCDateTime = None,
        minlatitude: float = None,
        maxlatitude: float = None,
        minlongitude: float = None,
        maxlongitude: float = None,
        latitude: float = None,
        longitude: float = None,
        minradius: float = None,
        maxradius: float = None,
        mindepth: float = None,
        maxdepth: float = None,
        minmagnitude: float = None,
        maxmagnitude: float = None,
        magnitudetype: str = None,
        eventtype: str = None,
        includeallorigins: bool = None,
        includearrivals: bool = None,
        eventid: str = None,
        limit: int = None,
        offset: int = None,
        orderby: bool = None,
        contributor: str = None,
        updatedafter: UTCDateTime = None,
        asquery: bool = False,
        **kwargs,
    ):
        """
        Query event data.

        >>> cat = client.get_events(eventid=609301)

        The return value is a :class:`~obspy.core.event.Catalog` object
        which can contain any number of events.

        >>> t1 = UTCDateTime("2001-01-07T00:00:00")
        >>> t2 = UTCDateTime("2001-01-07T03:00:00")
        >>> cat = client.get_events(starttime=t1, endtime=t2, minmagnitude=4,
        ...                         contributor="ISC")
        >>> print(cat)
        3 Event(s) in Catalog:
        2001-01-07T02:55:59.290000Z |  +9.801,  +76.548 | 4.9 mb
        2001-01-07T02:35:35.170000Z | -21.291,  -68.308 | 4.4 mb
        2001-01-07T00:09:25.630000Z | +22.946, -107.011 | 4.0 mb

        starttime : obspy.UTCDateTime, optional [Origin]
            Limit to events on or after the specified start time.
        endtime : obspy.UTCDateTime optional [Origin]
            Limit to events on or before the specified end time.
        minlatitude : float, optional [Origin]
            Limit to events with a latitude larger than the specified minimum.
        maxlatitude : float, optional [Origin]
            Limit to events with a latitude smaller than the specified
            maximum.
        minlongitude : float, optional [Origin]
            Limit to events with a longitude larger than the specified
            minimum.
        maxlongitude : float, optional [Origin]
            Limit to events with a longitude smaller than the specified
            maximum.
        latitude : float, optional [Origin]
            Specify the latitude to be used for a radius search.
            Not currently implemented.
        longitude : float, optional [Origin]
            Specify the longitude to the used for a radius search.
            Not currently implemented.
        minradius : float, optional [Origin]
            Limit to events within the specified minimum number of degrees
            from the geographic point defined by the latitude and longitude
            parameters.
            Not currently implemented.
        maxradius : float, optional [Origin]
            Limit to events within the specified maximum number of degrees
            from the geographic point defined by the latitude and longitude
            parameters.
            Not currently implemented.
        mindepth : float, optional [Origin]
            Limit to events with depth, in kilometers, larger than the
            specified minimum.
        maxdepth : float, optional [Origin]
            Limit to events with depth, in kilometers, smaller than the
            specified maximum.
        minmagnitude : float, optional [Origin, Netmag]
            Limit to events with a magnitude larger than the specified minimum.
        maxmagnitude : float, optional [Origin, Netmag]
            Limit to events with a magnitude smaller than the specified maximum.
        magnitudetype : str, optional [Origin, Netmag]
            Specify a magnitude type to use for testing the minimum and maximum limits.  If not
            provided, any magnitude range constraints are applied to all magnitude types. Netmag
            table is required for magnitudes other than 'ml', 'mb', or 'ms'.
            Wildcards are accepted.
        eventtype: str, optional [Origin]
            Limit to events with a specified event type. Multiple types are comma-separated
            e.g., `"earthquake,quarry blast"`. Allowed values are from QuakeML.
            See `obspy.core.event.header.EventType` for a list of allowed event types.
        includeallorigins : bool, optional (Origin [, Event])
            Specify if all origins for the event should be included. Default is False,
            which returns the preferred origin only and requires the Origin and Event table.
        includeallmagnitudes : bool, optional [ignored]
            KB Core has no concept of a preferred magnitude, so all magnitudes are always returned
            (i.e. always True). If more refined magnitudes are desired, users are
            recommended to also specify a magnitudetype and/or contributor.
        includearrivals : bool, optional [Assoc, Arrival]
            Specify if phase arrivals should be included. Default is False.
        eventid : str or int, optional [Event | Origin]
            Select a specific event by ID (evid), or comma-separated list of IDs.
            e.g. 1234 or '1234,5678'.  If provided, all other parameters are ignored.
        limit : int, optional [not yet implemented]k
            Limit the results to the specified number of events.
        offset : int, optional [not yet implemented]
            Return results starting at the event count specified, starting at 1.
        orderby : str, optional [Origin]
            Order the result by time or magnitude with the following possibilities:

            * time: order by origin descending time [not yet implemented]
            * time-asc: order by origin ascending time [not yet implemented]
            * magnitude: order by descending magnitude [ignored]
                KB Core events doen't have a preferred magnitude, so sorting is ignored.
            * magnitude-asc: order by ascending magnitude [ignored]
                See above.

        catalog : str, optional [ignored]
            KB Core tables have no concept of a catalog. This parameter is ignored.
            See 'contributor' below.
        contributor : str, optional [Origin]
            Limit to events contributed by a specified contributor.
            Matches strings inside the 'auth' field in the Origin table.  Catalog sources
            are embedded within this field, so add them here with wildcards, like '*ISC*'.
        updatedafter : obspy.UTCDateTime, optional [Origin]
            Limit to events updated after the specified time.
            KB Core doesn't keep track of updates, so this parameter filters Origin.lddate,
            the date the origin was added to the database.
        asquery : bool
            Return the raw SQLAlchemy query instead of direct results.

        Returns
        -------
        result : obspy.Catalog or sqlalchemy.orm.Query instance

        Raises
        ------
        ValueError
            Missing or improper inputs.

        """
        try:
            Origin = self.tables["origin"]
            Netmag = self.tables["netmag"]
            Event = self.tables["event"]
        except KeyError:
            msg = "Event, Origin, and Netmag tables required."
            raise ValueError(msg)

        # Stamag = self.tables.get("stamag", None)
        Arrival = self.tables.get("arrival", None)
        Assoc = self.tables.get("assoc", None)

        # characterize which inputs were provided
        timeparams = any([starttime, endtime])
        boxparams = any([minlongitude, maxlongitude, minlatitude, maxlatitude])
        radialparams = any([latitude, longitude, minradius, maxradius])
        magparams = any([minmagnitude, maxmagnitude, magnitudetype])

        # check which optional tables we need
        useArrival = includearrivals

        # check for nonsense inputs
        if eventid and (magparams or boxparams or radialparams or timeparams):
            msg = "If eventid is specified, no other parameters are used."
            warnings.warn(msg)

        if boxparams and radialparams:
            msg = "Incompatible inputs: using both lat/lon and radius ranges not allowed"
            raise ValueError(msg)

        if useArrival and (not Arrival or not Assoc):
            msg = "Arrival and Assoc tables required for includeallarrivals."
            raise ValueError(msg)

        if orderby not in ("time", "time-asc", "magnitude", "magnitude-asc", None):
            msg = "orderby must be one of ('time', 'time-asc', 'magnitude', 'magnitude-asc')"
            raise ValueError(msg)

        if eventtype and (eventtype.lower() not in EventType):
            msg = f"eventtype '{eventtype}' not recognized.  choose from {list(KBCORE_EVENT_TYPE.keys())}"
            raise ValueError(msg)

        # normalize inputs for event query functions
        times = _None_if_none(starttime, endtime)
        region = _None_if_none(minlongitude, maxlongitude, minlatitude, maxlatitude)
        radius = _None_if_none(latitude, longitude, minradius, maxradius)
        depth = _None_if_none(mindepth, maxdepth)
        prefor = not includeallorigins
        magnitudetype = 'all' if magparams and not magnitudetype else magnitudetype
        magnitudes = {magnitudetype: (minmagnitude, maxmagnitude)} if magparams else {}
        auth = contributor
        if eventtype:
            # may be multiple eventtypes, which may correspond to multiple KB Core etypes
            etype_set = {}
            for e in eventtype.split(','):
                ietypes = KBCORE_EVENT_TYPE.get(e, e).split(',')
                etype_set.update({*ietypes})
            etype = ','.join(etype_set) # rejoin the unique set with commas
        else:
            etype = None

        # turn string event IDs into integer evid list
        evid = [int(e) for e in eventid.split(",")] if eventid else None

        # build the query (finally)

        # geographic / categorical stuff
        q = self.session.query(Event, Origin)
        qe = events.filter_events(q,
                                 region=region,
                                 times=times,
                                 depth=depth,
                                 evid=evid,
                                 prefor=prefor,
                                 auth=auth,
                                 etype=etype,
        )
        # [(event, origin, netmag)]

        if updatedafter:
            qe = qe.filter(Origin.lddate > updatedafter)

        # magnitude stuff
        # return all magnitudes...
        qm = qe.add_entity(Netmag)
        if magnitudes:
            # ...unless certain ones were specified
            qm = events.filter_magnitudes(qm, **magnitudes)

        # arrival stuff
        if useArrival:
            # unfortunately, produces a cartesian join with netmags, resulting in repeated
            # events, origins, netmags for each arrival/origin
            qa = qe.add_entity(Assoc).add_entity(Arrival)
            qa = events.filter_arrivals(qa)
        else:
            qa = None
        # [(event, origin, netmag, assoc, arrival)]


        # XXX: implement proper preferred origin sorting, limit, offset
        # if orderby == "time":
            # q = q.order_by(Origin.time.desc())
        # elif orderby == "time-asc":
            # q = q.order_by(Origin.time.asc())
        # elif orderby == "magnitude":
            # q = q.order_by(Netmag.magnitude.desc())
        # elif orderby == "magnitude-asc":
            # q = q.order_by(Netmag.magnitude.asc())

        # TODO: how to offset/limit just the Event.evids?  use itertools sorted, groupby, islice?
        # .limit/offset on an ordered subquery?
        # q = q.limit(limit) if limit else q
        # q = q.offset(offset) if offset else q

        if asquery:
            result = qm, qa
        else:
            queries = [q for q in [qm, qa] if q]
            result = catalog(*queries)

        return result


    def get_stations(
        self,
        starttime: UTCDateTime = None,
        endtime: UTCDateTime = None,
        startbefore: UTCDateTime = None,
        startafter: UTCDateTime = None,
        endbefore: UTCDateTime = None,
        endafter: UTCDateTime = None,
        network: str = None,
        station: str = None,
        location: str = None,
        channel: str = None,
        minlatitude: float = None,
        maxlatitude: float = None,
        minlongitude: float = None,
        maxlongitude: float = None,
        latitude: float = None,
        longitude: float = None,
        minradius: float = None,
        maxradius: float = None,
        level: str = None,
        includerestricted: bool = None,
        includeavailability: bool = None,
        updatedafter: UTCDateTime = None,
        matchtimeseries: bool = None,
        filename: str = None,
        format: str = "xml",
        **kwargs
    ):
        """
        Query station station data.

        Examples
        --------

        >>> starttime = UTCDateTime("2001-01-01")
        >>> endtime = UTCDateTime("2001-01-02")
        >>> inventory = client.get_stations(network="IU", station="A*",
        ...                                 starttime=starttime,
        ...                                 endtime=endtime)
        >>> print(inventory)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Inventory created at ...
            Created by: IRIS WEB SERVICE: fdsnws-station | version: ...
                        ...
            Sending institution: IRIS-DMC (IRIS-DMC)
            Contains:
                    Networks (1):
                            IU
                    Stations (3):
                            IU.ADK (Adak, Aleutian Islands, Alaska)
                            IU.AFI (Afiamalu, Samoa)
                            IU.ANMO (Albuquerque, New Mexico, USA)
                    Channels (0):

        The result is an `obspy.core.inventory.inventory.Inventory`
        object which models a StationXML file.

        The `level` argument determines the amount of returned information.
        `level="station"` is useful for availability queries whereas
        `level="response"` returns the full response information for the
        requested channels. `level` can furthermore be set to `"network"`
        and `"channel"`.

        >>> inventory = client.get_stations(
        ...     starttime=starttime, endtime=endtime,
        ...     network="IU", sta="ANMO", loc="00", channel="*Z",
        ...     level="response")
        >>> print(inventory)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
        Inventory created at ...
            Created by: IRIS WEB SERVICE: fdsnws-station | version: ...
                        ...
            Sending institution: IRIS-DMC (IRIS-DMC)
            Contains:
                Networks (1):
                    IU
                Stations (1):
                    IU.ANMO (Albuquerque, New Mexico, USA)
                Channels (4):
                    IU.ANMO.00.BHZ, IU.ANMO.00.LHZ, IU.ANMO.00.UHZ,
                    IU.ANMO.00.VHZ

        Parameters
        ----------
        starttime : UTCDateTime
            Limit to metadata epochs starting on or after the specified start time.
        endtime : UTCDateTime
            Limit to metadata epochs ending on or before the specified end time.
        startbefore : .UTCDateTime
            Limit to metadata epochs starting before specified time.
        startafter : UTCDateTime
            Limit to metadata epochs starting after specified time.
        endbefore : UTCDateTime
            Limit to metadata epochs ending before specified time.
        endafter : UTCDateTime
            Limit to metadata epochs ending after specified time.
        network : str
            Select one or more network codes. Can be SEED network codes or data
            center defined codes. Multiple codes are comma-separated (e.g.
            "IU,TA").
        station : str
            Select one or more SEED station codes. Multiple codes are comma-separated
            (e.g. "ANMO,PFO").
        location : str
            Select one or more SEED location identifiers. Multiple identifiers
            are comma-separated (e.g. "00,01").  As a special case "--"
            (two dashes) will be translated to a string of two space characters
            to match blank location IDs.
        channel : str
            Select one or more SEED channel codes. Multiple codes are
            comma-separated (e.g. "BHZ,HHZ").
        minlatitude : float
            Limit to stations with a latitude larger than the specified minimum.
        maxlatitude : float
            Limit to stations with a latitude smaller than the specified maximum.
        minlongitude : float
            Limit to stations with a longitude larger than the specified minimum.
        maxlongitude : float
            Limit to stations with a longitude smaller than the specified maximum.
        latitude : float
            Specify the latitude to be used for a radius search.
        longitude : float
            Specify the longitude to be used for a radius search.
        minradius : float
            Limit results to stations within the specified minimum number of
            degrees from the geographic point defined by the latitude and
            longitude parameters.
        maxradius : float
            Limit results to stations within the specified maximum number of
            degrees from the geographic point defined by the latitude and
            longitude parameters.
        level : str
            Specify the level of detail for the results ("network", "station",
            "channel", "response"), e.g. specify "response" to get full
            information including instrument response for each channel.
        includerestricted : bool
            Specify if results should include information for restricted stations.
        includeavailability : bool
            Specify if results should include information about time series data availability.
        updatedafter : UTCDateTime
            Limit to metadata updated after specified date; updates are data center specific.
        matchtimeseries : bool
            Only include data for which matching time series data is available.
        filename : str or file
            If given, the downloaded data will be saved there instead of being
            parsed to an ObsPy object. Thus it will contain the raw data from
            the webservices.
        format : str
            The format in which to request station information. "xml"
            (StationXML) or "text" (FDSN station text format). XML has more
            information but text is much faster.

        Returns
        -------
        Inventory
            Inventory with requested station information.

        Any additional keyword arguments will be passed to the webservice as
        additional arguments. If you pass one of the default parameters and the
        webservice does not support it, a warning will be issued. Passing any
        non-default parameters that the webservice does not support will raise
        an error.

        """
        pass

    def get_waveforms(
        self,
        network,
        station,
        location,
        channel,
        starttime,
        endtime,
        quality=None,
        minimumlength=None,
        longestonly=None,
        attach_response=False,
        asquery=False,
        **kwargs
    ):
        """
        Get waveforms from the database.

        Requires the data and response directories in 'dir' and 'dfile' columns
        to be available/mounted on the client machine.

        network : str
            Select one or more network codes. Can be SEED network codes or data
            center defined codes. Multiple codes are comma-separated
            (e.g. "IU,TA"). Wildcards are allowed.
        station : str
            Select one or more SEED station codes. Multiple codes are
            comma-separated (e.g. "ANMO,PFO"). Wildcards are allowed.
        location : str
            Select one or more SEED location identifiers. Multiple identifiers
            are comma-separated (e.g. "00,01"). Wildcards are allowed.
        channel : str
            Select one or more SEED channel codes. Multiple codes are
            comma-separated (e.g. "BHZ,HHZ").
        starttime : obspy.core.utcdatetime.UTCDateTime
            Limit results to time series samples on or after the specified start
            time
        endtime : obspy.core.utcdatetime.UTCDateTime
            Limit results to time series samples on or before the specified end
            time
        quality : str, optional
            Select a specific SEED quality indicator, handling is data center
            dependent. Not currently implemented.
        minimumlength : float, optional
            Limit results to continuous data segments of a minimum length
            specified in seconds.
        longestonly : bool, optional
            Limit results to the longest continuous segment per channel.
        attach_response : bool
            Specify whether the station web service should be used to
            automatically attach response information to each trace in the
            result set. A warning will be shown if a response can not be found.
            Not currently implemented.
        asquery : bool, optional
            If True, doesn't return a Stream, but instead returns the SQLAlchemy
            Query instance that was produced by the passed parameters.
            for a channel. Does nothing if output to a file was specified.

        Any additional keyword arguments will be passed to the query engine as
        additional arguments. If you pass one of the default parameters and the
        query engine does not support it, a warning will be issued. Passing any
        non-default parameters that the query engine does not support will raise
        an error.

        Examples
        --------
        >>> t1 = UTCDateTime("2010-02-27T06:30:00.000")
        >>> t2 = t1 + 5
        >>> st = client.get_waveforms("IU", "A*", "1?", "LHZ", t1, t2)
        >>> print(st)  # doctest: +ELLIPSIS
        3 Trace(s) in Stream:
        IU.ADK.10.LHZ  | 2010-02-27T06:30:00.069538Z - ... | 1.0 Hz, 5 samples
        IU.AFI.10.LHZ  | 2010-02-27T06:30:00.069538Z - ... | 1.0 Hz, 5 samples
        IU.ANMO.10.LHZ | 2010-02-27T06:30:00.069538Z - ... | 1.0 Hz, 5 samples

        """
        # Use ``attach_response=True`` to automatically add response information
        # to each trace. This can be used to remove response using
        # :meth:`~obspy.core.stream.Stream.remove_response`.

        # >>> t = UTCDateTime("2012-12-14T10:36:01.6Z")
        # >>> st = client.get_waveforms("TA", "E42A", "*", "BH?", t+300, t+400,
        # ...                           attach_response=True)
        # >>> st.remove_response(output="VEL") # doctest: +ELLIPSIS
        # <obspy.core.stream.Stream object at ...>
        # >>> st.plot()  # doctest: +SKIP

        # longestonly : bool, optional
        #     Limit results to the longest continuous segment per channel.

        Wfdisc = self.tables["wfdisc"]  # required
        Affil = self.tables.get("affiliation")

        # Manage wildcarding and location codes before query.filter-ing.

        location = "" if location == "--" else location

        # Replace '*' and '?' with '%' and '_'
        wildcardables = (network, station, location, channel)
        wildcardables = [util.glob_to_like(item) for item in wildcardables]
        network, station, location, channel = wildcardables

        # turn any "comma lists" into Python lists
        listables = (network, station, location, channel)
        listables = [listable.split(",") for listable in listables]
        networks, stations, locations, channels = listables
        # even single strings are now a single element list

        # XXX: we decided not to support this
        # In CSS-like schema, location codes are often just tacked onto channel
        # codes.  channel may now included multiple wildcards.  Do a cartesian
        # product of location codes tacked at the end of channel codes.
        # channels = [chan + loc for chan in channels for loc in locations]

        t1, t2 = starttime.timestamp, endtime.timestamp

        # Build the query
        q = req.get_wfdisc_rows(
            self.session, Wfdisc, sta=stations, chan=channel, t1=t1, t2=t2, asquery=True
        )

        # q = self.session.query(Wfdisc)

        # # apply string filters/expressions
        # q = q.filter(util.string_expression(Wfdisc.sta, stations))
        # q = q.filter(util.string_expression(Wfdisc.chan, channels))

        # CHUNKSIZE = 24 * 60 * 60
        # q = q.filter(Wfdisc.time.between(t1 - CHUNKSIZE, t2))
        # q = q.filter(Wfdisc.time > t1)
        # q = q.filter(Wfdisc.time <= t2)

        if networks:
            try:
                q = q.filter(Wfdisc.sta == Affil.sta)
                q = q.filter(util.string_expression(Affil.net, networks))
            except AttributeError:
                # Affil is None and has no ".sta" or ".net"
                msg = "No Affiliation table provided for network filtering."
                log.error(msg)
                # XXX: change this to pisces.exc.MissingTableError
                raise ValueError(msg)

        if minimumlength:
            q = q.filter((Wfdisc.endtime - Wfdisc.time) > minimumlength)

        if asquery:
            out = q
        else:
            out = req.wfdisc_rows_to_stream(q, starttime, endtime)
        # log.debug(util.literal_sql(self.session, q))

        # st = Stream()
        # for wf in q:
        #     try:
        #         tr = wfdisc2trace(wf)
        #         st.append(tr)
        #     except IOError:
        #         msg = "Unable to read file: dir = {}, dfile = {}"
        #         log.error(msg.format(wf.dir, wf.dfile)) # TODO: append action IOError message, too

        # st.trim(starttime, endtime)
        # # TODO: merge them?

        return out
