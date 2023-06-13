# -*- coding: utf-8 -*-
"""
Pisces Client mirrors the ObsPy FDSN Client interface.

"""
import logging
import os

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from obspy import Stream, UTCDateTime

import pisces as ps
import pisces.request as req
from pisces.io.trace import wfdisc2trace
from pisces import util

log = logging.getLogger(__name__)

# client = DBClient(session_or_config_or_URI, **tables)
# get network-level info for stations containing BH? in a region. 
# returns joined sitechan, site, affil, and network
# q = client.stations(region=[W, E, S, N], channels='BH?').networks(pref_nets=('II','IU','ISC'))
# get responses for all BH? stations in II
# q = client.networks(networks=['II']).stations(channels='BH?').responses()


def _None_if_none(iterable):
    return None if all([val is None for val in iterable]) else iterable


def origins_to_fdsntext(origins, header=False):
    """ Convert a SQLAlchemy Origin instances to FDSN event text.

    #EventID | Time | Latitude | Longitude | Depth/km | Author | Catalog | Contributor | ContributorID | MagType | Magnitude | MagAuthor | EventLocationName
    #origin.orid|origin.time|origin.lat|origin.lon|origin.depth|netmag.auth|netmag.auth|netmag.auth|netmag.magtype|netmag.magnitude|sregion.srname or event.evname
    #origin.orid|origin.time|origin.lat|origin.lon|origin.depth|origin.auth|origin.auth|origin.auth|('ml','ms','mb')|origin.('ml','ms','mb')|sregion.srname or event.evname
    header_string = '#EventID|Time|Latitude|Longitude|Depth/km|Author|Catalog|Contributor|ContributorID|MagType|Magnitude|MagAuthor|EventLocationName'

    """
    header_string = "EventID | Time | Latitude | Longitude | Depth/km | Author | Catalog | Contributor | ContributorID | MagType | Magnitude | MagAuthor | EventLocationName"
    # this needs to get MagType in there
    origin_columns = ('orid', 'time', 'lat', 'lon', 'depth', 'auth', 'auth',
                      'auth', 'orid', 'mb', 'mb', 'auth', 'grn')
    rows = ['|'.join(str(getattr(origin, column, '-')) for column in origin_columns)
            for origin in origins]

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
        if type(dburl_or_session) is str:
            engine = sa.create_engine(dburl_or_session)
            session = Session(engine)
        else:
            session = dburl_or_session

        # this is just a test, will fail early if the connection is misconfigured
        # session.bind.connect()

        self.session = session
        self.tables = tables


    def __repr__(self):
        repr_str = "<Client({!r})>"

        return repr_str.format(self.session.bind.url)



    def get_events(self, starttime=None, endtime=None, minlatitude=None, maxlatitude=None,
                   minlongitude=None, maxlongitude=None, latitude=None, longitude=None, 
                   minradius=None, maxradius=None, mindepth=None, maxdepth=None, 
                   minmagnitude=None, maxmagnitude=None, magnitudetype=None, eventtype=None, 
                   includeallorigins=None, includeallmagnitudes=None, includearrivals=None, 
                   eventid=None, limit=None, offset=None, orderby=None, catalog=None, 
                   contributor=None, updatedafter=None, filename=None, **kwargs):
        """
        Query event data.

        >>> cat = client.get_events(eventid=609301)

        The return value is a :class:`~obspy.core.event.Catalog` object
        which can contain any number of events.

        >>> t1 = UTCDateTime("2001-01-07T00:00:00")
        >>> t2 = UTCDateTime("2001-01-07T03:00:00")
        >>> cat = client.get_events(starttime=t1, endtime=t2, minmagnitude=4,
        ...                         catalog="ISC")
        >>> print(cat)
        3 Event(s) in Catalog:
        2001-01-07T02:55:59.290000Z |  +9.801,  +76.548 | 4.9 mb
        2001-01-07T02:35:35.170000Z | -21.291,  -68.308 | 4.4 mb
        2001-01-07T00:09:25.630000Z | +22.946, -107.011 | 4.0 mb

        starttime : obspy.core.utcdatetime.UTCDateTime, optional
            Limit to events on or after the specified start time.
        endtime : obspy.core.utcdatetime.UTCDateTime optional
            Limit to events on or before the specified end time.
        minlatitude : float, optional
            Limit to events with a latitude larger than the specified minimum.
        maxlatitude : float, optional
            Limit to events with a latitude smaller than the specified
            maximum.
        minlongitude : float, optional
            Limit to events with a longitude larger than the specified
            minimum.
        maxlongitude : float, optional
            Limit to events with a longitude smaller than the specified
            maximum.
        latitude : float, optional
            Specify the latitude to be used for a radius search.
        longitude : float, optional
            Specify the longitude to the used for a radius search.
        minradius : float, optional
            Limit to events within the specified minimum number of degrees
            from the geographic point defined by the latitude and longitude
            parameters.
        maxradius : float, optional
            Limit to events within the specified maximum number of degrees
            from the geographic point defined by the latitude and longitude
            parameters.
        mindepth : float, optional
            Limit to events with depth, in kilometers, larger than the
            specified minimum.
        maxdepth : float, optional
            Limit to events with depth, in kilometers, smaller than the
            specified maximum.
        minmagnitude : float, optional
            Limit to events with a magnitude larger than the specified
            minimum.
        maxmagnitude : float, optional
            Limit to events with a magnitude smaller than the specified
            maximum.
        magnitudetype : str, optional
            Specify a magnitude type to use for testing the minimum and
            maximum limits.
        includeallorigins : bool, optional
            Specify if all origins for the event should be included. Default
            returns the preferred origin only.
            Requires Event table.
        includeallmagnitudes : bool, optional
            Specify if all magnitudes for the event should be included,
            default is data center dependent but is suggested to be the
            preferred magnitude only.
            Requires Netmag table.
        includearrivals : bool, optional
            Specify if phase arrivals should be included.
            Requires Assoc and Arrival tables.
        eventid : str or int, optional
            Select a specific event by ID (evid), or comma-separated list of IDs.
            e.g. 1234 or '1234,5678'
        limit : int, optional
            Limit the results to the specified number of events.
        offset : int, optional
            Return results starting at the event count specified, starting
            at 1.
        orderby : str, optional
            Order the result by time or magnitude with the following
            possibilities:

            * time: order by origin descending time
            * time-asc: order by origin ascending time
            * magnitude: order by descending magnitude
            * magnitude-asc: order by ascending magnitude

        catalog : str, optional
            Limit to events from a specified catalog
            Looks for catalog inside of origin.auth.
        contributor : str, optional
            Limit to events contributed by a specified contributor.
            Looks for contributer inside of origin.auth.
        updatedafter : obspy.core.utcdatetime.UTCDateTime, optional
            Limit to events updated after the specified time.
        format : str ["xml" (StationXML) | "text" (FDSN station text format) | query (raw SQLAlchey query)]
            The format in which to request station information. 
        asquery : bool
            Return results as a raw SQLAlchemy query instead of the results proper.

        Any additional keyword arguments will be passed to the webservice as
        additional arguments. If you pass one of the default parameters and the
        webservice does not support it, a warning will be issued. Passing any
        non-default parameters that the webservice does not support will raise
        an error.

        """
        Origin = self.tables['origin'] #required
        Event = self.tables.get('event')
        Netmag = self.tables.get('netmag')
        Stamag = self.tables.get('stamag')
        Arrival = self.tables.get('arrival')
        Assoc = self.tables.get('assoc')

        # Origin filters
        time_span = _None_if_none((starttime, endtime))
        region = _None_if_none((minlongitude, maxlongitude, minlatitude, maxlatitude))
        radius = _None_if_none((latitude, longitude, minradius, maxradius))
        depth = _None_if_none((mindepth, maxdepth))

        if region and radius:
            msg = "Incompatible inputs: using both lat/lon and radius ranges not allowed"
            raise ValueError(msg)

        # Event filters
        if includeallorigins in (None, False):
            prefor = True
        else:
            prefor = False

        # turn string event IDs into integer evid list
        if eventid:
            evids = [int(evid) for evid in eventid.split(',')]
        else:
            evids = None

        # Netmag filters
        mag = _None_if_none((minmagnitude, maxmagnitude))
        # if magnitudetype isn't in Origin, we'll need Netmag
        # TODO: we need remove case-sensitivity here.
        if magnitudetype:
            useNetmag = True if magnitudetype not in Origin.__tables__.columns else False
        else:
            useNetmag = False

        # we may need _all_ of Netmag
        useAllNetMag = includeallmagnitudes
        magtype = magnitudetype


        q = req.get_events(self.session, Origin, event=Event, region=region, depth=depth, 
                           etime=time_span, evids=evids, prefor=prefor, asquery=True)

        # q = req.get_magnitudes(Origin, Netmag, query=None, **magnitudes)

        # magnitude
        if any([magnitudetype, minmagnitude, maxmagnitude]):
            mag = {magnitudetype: (minmagnitude, maxmagnitude)}
        else:
            mag = None

        if includeallmagnitudes:
            try:
                q = q.add_entity(Netmag)
            except sa.exc.NoInspectionAvailable:
                msg = "Netmag table is required for 'includeallmagnitudes`."
                raise ps.exc.RequiredTableError(msg)
            q = q.filter(Origin.orid == Netmag.orid)

        q = q.filter(Origin.auth.contains(catalog)) if catalog else q
        q = q.filter(Origin.auth.contains(contributor)) if contributor else q

        if updatedafter:
            q = q.filter(Origin.lddate > updatedafter.timestamp)

        if includeallmagnitudes:
            try:
                q = q.add_entity(Netmag)
            except sa.exc.NoInspectionAvailable:
                msg = "Netmag table is required for 'includeallmagnitudes`."
                raise ps.exc.RequiredTableError(msg)
            q = q.filter(Origin.orid == Netmag.orid)

        q = q.filter(Origin.auth.contains(catalog)) if catalog else q
        q = q.filter(Origin.auth.contains(contributor)) if contributor else q

        if updatedafter:
            q = q.filter(Origin.lddate > updatedafter.timestamp)

        if orderby in ('time', 'time-asc', 'magnitude', 'magnitude-asc', None):
            if orderby == 'time':
                q = q.order_by(Origin.time.desc())
            elif orderby == 'time-asc':
                q = q.order_by(Origin.time.asc())
            elif orderby == 'magnitude':
                # TODO: DRY
                try:
                    q = q.order_by(Netmag.mag.desc())
                except AttributeError:
                    msg = "Netmag table is required for orderby : {}".format(orderby)
                    raise ps.exc.RequiredTableError(msg)
            elif orderby == 'magnitude-asc':
                try:
                    q = q.order_by(Netmag.mag.asc())
                except AttributeError:
                    msg = "Netmag table is required for orderby : {}".format(orderby)
                    raise ps.exc.RequiredTableError(msg)
        else:
            msg = "Unrecognized orderby : {}".format(orderby)
            raise ValueError(msg)

        if includearrivals:
            # output is now (origins, arrivals) or (origins, netmags, arrivals)
            try:
                q.add_entity(Arrival)
                q.filter(Origin.orid == Assoc.orid, Assoc.arid == Arrival.arid)
            except (sa.exc.NoInspectionAvailable, AttributeError):
                msg = "Assoc and Arrival table required for 'includeallarrivals`."
                raise ps.exc.RequiredTableError(msg)

        q = q.limit(limit) if limit else q
        q = q.offset(offset) if offset else q

        if kwargs.get('asquery'):
            result = q
        else:
            result = q.all()

        return result


    def get_stations(self,
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
                     **kwargs):
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


    def get_waveforms(self, network, station, location, channel, starttime,
                      endtime, quality=None, minimumlength=None,
                      longestonly=None, attach_response=False, asquery=False,
                      **kwargs):
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

        Wfdisc = self.tables['wfdisc'] # required
        Affil = self.tables.get('affiliation')

        # Manage wildcarding and location codes before query.filter-ing.

        location = '' if location == '--' else location

        # Replace '*' and '?' with '%' and '_'
        wildcardables = (network, station, location, channel)
        wildcardables = [util.glob_to_like(item) for item in wildcardables]
        network, station, location, channel = wildcardables

        # turn any "comma lists" into Python lists
        listables = (network, station, location, channel)
        listables = [listable.split(',') for listable in listables]
        networks, stations, locations, channels = listables
        # even single strings are now a single element list

        # XXX: we decided not to support this
        # In CSS-like schema, location codes are often just tacked onto channel
        # codes.  channel may now included multiple wildcards.  Do a cartesian
        # product of location codes tacked at the end of channel codes.
        # channels = [chan + loc for chan in channels for loc in locations]

        t1, t2 = starttime.timestamp, endtime.timestamp

        # Build the query
        q = req.get_wfdisc_rows(self.session, Wfdisc, sta=stations, chan=channel, t1=t1, t2=t2, asquery=True)

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
            q = q.filter((Wfdisc.endtime - Wfdisc.time ) > minimumlength)

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
