# -*- coding: utf-8 -*-
"""
Pisces Client mirrors the ObsPy FDSN Client interface.

"""
import logging
import os

import sqlalchemy as sa
from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import Session
from obspy import Stream
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.engine.url import URL, make_url
from obspy import Stream

import pisces as ps
import pisces.request as req
from pisces.io.trace import wfdisc2trace

log = logging.getLogger(__name__)

def _glob_to_like(text, escape='\\'):
    # replace string '*' or '?' glob characters with SQL '%' or '_' LIKE characters,
    # escaping any existing literal '%' or '_' characters.
    text = text.replace('_', escape + '_').replace('?', '_')
    text = text.replace('%', escape + '%').replace('*', '%')

    return text


def origins_to_fdsntext(origins, header=False):
    """ Convert a SQLAlchemy Origin instances to FDSN event text.

    #EventID | Time | Latitude | Longitude | Depth/km | Author | Catalog | Contributor | ContributorID | MagType | Magnitude | MagAuthor | EventLocationName
    #origin.orid|origin.time|origin.lat|origin.lon|origin.depth|netmag.auth|netmag.auth|netmag.auth|netmag.magtype|netmag.magnitude|sregion.srname or event.evname
    #origin.orid|origin.time|origin.lat|origin.lon|origin.depth|origin.auth|origin.auth|origin.auth|('ml','ms','mb')|origin.('ml','ms','mb')|sregion.srname or event.evname
    header_string = '#EventID|Time|Latitude|Longitude|Depth/km|Author|Catalog|Contributor|ContributorID|MagType|Magnitude|MagAuthor|EventLocationName'

    """
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
        >>> client = Client('oracle://dbserver.somewhere.com:8080/mydb')
        >>> client = Client('oracle://scott@dbserver.somewhere.com:8080/mydb')
        >>> client = Client('oracle://scott:tiger@dbserver.somewhere.com:8080/mydb')
        >>> client = Client(session)

        >>> from myschema import Origin, Site
        >>> client = Client(session, origin=Origin, site=Site)

        >>> from pisces import crud
        >>> tables = crud.make_tables('origin', 'site', owner='global')
        >>> client = Client(session, **tables)

        """
        if kwargs.get('session', None):
            session = session
        else:
            engine = sa.create_engine(dburl_or_session)
            session = Session(engine)

        # this is just a test, will fail early if the connection is misconfigured
        session.bind.connect()

        self.session = session
        self.tables = tables


    def __repr__(self):
        repr_str = "<Client({!r})>"

        return repr_str.format(self.session.bind.url)


    def load_tables(self, **tables):
        """
        Load core tables.

        Tables are given as key=value pairs as in:
        load_tables(wfdisc='global.wfdisc_raw', origin='location.origin')

        Raises
        ------
        sqlalchemy.exc.NoSuchTableError
            Table doesn't exist.

        """
        # TODO: add the tables as attributes?
        # TODO: if isinstance(table, DeclarativeBase): just set it as attribute
        # XXX: fails for no primary key.  use get_tables syntax.
        for coretable, tablename in tables.iteritems():
            self.tables[coretable] = ps.get_tables(self.session.bind, 
                                                   [tablename], 
                                                   metadata=self.metadata)[0]
        
    def get_events(self, region=None, deg=None, km=None, swath=None, mag=None, 
            depth=None, etype=None, orids=None, evids=None, prefor=False):
        """ Get Origin table rows.

        For further explanation, see: pisces.request.get_events

        """
        #origin = getattr(self, 'origin', None)
        origin = self.tables.get('origin')
        origin = self.tables.get('event', None)

        recs = req.get_events(self.session, origin, event=event, region=region, 
                              deg=deg, km=km, swath=swath, mag=mag, depth=depth,
                              etime=etime, orids=orids, evids=evids, 
                              prefor=prefor)
        return recs

    def get_stations(self, stations=None, channels=None, nets=None, loc=None, 
            region=None, deg=None, km=None, swath=None, stime=None):
        """
        Get Site table rows.

        For further explanation, see: pisces.request.get_stations

        """
        site = self.tables.get('site')
        sitechan = self.tables.get('sitechan', None)
        affiliation = self.tables.get('affiliation', None)

        recs = req.get_stations(self.session, site, sitechan=sitechan, 
                affiliation=affiliation, stations=stations, channels=channels,
                nets=nets, loc=loc, region=region, deg=deg, km=km, swath=swath,
                stime=stime)

        return recs


        # TODO: check that magnitudetype is in Origin, if not includeallmagnitudes

        prefor = includeallorigins or False
        orids = None

        if eventid:
            evids = [eventid]
        else:
            evids = None

        # TODO: get netmag in get_events
        q = req.get_events(self.session, Origin, Event, region=region, deg=deg,
                           km=km, depth=depth, etime=etime, orids=orids,
                           evids=evids, prefor=prefor, asquery=True)

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

        if 'asquery' in kwargs:
            result = q
        else:
            result = q.all()

        return result


    def get_stations(self, starttime=None, endtime=None, startbefore=None,
                     startafter=None, endbefore=None, endafter=None,
                     network=None, station=None, location=None, channel=None,
                     minlatitude=None, maxlatitude=None, minlongitude=None,
                     maxlongitude=None, latitude=None, longitude=None,
                     minradius=None, maxradius=None, level=None,
                     includerestricted=None, includeavailability=None,
                     updatedafter=None, matchtimeseries=None, filename=None,
                     format="xml", **kwargs):
        """
        Request database arrivals.
        
        For further explanation, see: pisces.request.get_arrivals

        """
        arrival = self.tables.get('arrival')
        assoc = self.tables.get('assoc', None)

        recs = get_arrivals(self.session, arrival, assoc=assoc, 
                            stations=stations, channels=channels, atime=atime, 
                            phases=phases, arids=arids, orids=orids, auth=auth)

        return recs


    def get_waveforms(self, station=None, channel=None, starttime=None, 
            endtime=None, wfids=None):
        """
        Get waveforms. 

        For further explanation, see: pisces.request.get_waveforms

        The services can deal with UNIX style wildcards.

        >>> st = client.get_waveforms("IU", "A*", "1?", "LHZ", t1, t2)
        >>> print(st)  # doctest: +ELLIPSIS
        3 Trace(s) in Stream:
        IU.ADK.10.LHZ  | 2010-02-27T06:30:00.069538Z - ... | 1.0 Hz, 5 samples
        IU.AFI.10.LHZ  | 2010-02-27T06:30:00.069538Z - ... | 1.0 Hz, 5 samples
        IU.ANMO.10.LHZ | 2010-02-27T06:30:00.069538Z - ... | 1.0 Hz, 5 samples

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
        minimumlength : float, optional
            Limit results to continuous data segments of a minimum length
            specified in seconds.
        asquery : bool, optional
            If True, doesn't return a Stream, but instead returns the SQLAlchemy
            Query instance that was produced by the passed parameters.

        Any additional keyword arguments will be passed to the webservice as
        additional arguments. If you pass one of the default parameters and the
        webservice does not support it, a warning will be issued. Passing any
        non-default parameters that the webservice does not support will raise
        an error.

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

        # .. plot::

        #     from obspy import UTCDateTime
        #     from obspy.clients.fdsn import Client
        #     client = Client("IRIS")
        #     t = UTCDateTime("2012-12-14T10:36:01.6Z")
        #     st = client.get_waveforms("TA", "E42A", "*", "BH?", t+300, t+400,
        #                               attach_response=True)
        #     st.remove_response(output="VEL")
        #     st.plot()

        # longestonly : bool, optional
        #     Limit results to the longest continuous segment per channel.

        # TODO: this method needs to use request.get_waveforms

        Wfdisc = self.tables['wfdisc'] # required
        Affil = self.tables.get('affiliation')

        # Manage wildcarding and location codes before query.filter-ing.

        location = '' if location == '--' else location

        # Replace '*' and '?' with '%' and '_'
        wildcardables = (network, station, location, channel)
        wildcardables = [util.glob_to_like(item) for item in wildcardables]
        network, station, location, channel = wildcardables

        # turn any comma "lists" into Python lists
        # even single strings are now a single element list
        listables = (network, station, location, channel)
        listables = [listable.split(',') for listable in listables]
        networks, stations, locations, channels = listables

        # In CSS-like schema, location codes are often just tacked onto channel
        # codes.  channel may now included multiple wildcards.  Do a cartesian
        # product of location codes tacked at the end of channel codes.
        channels = [chan + loc for chan in channels for loc in locations]

        t1, t2 = starttime.timestamp, endtime.timestamp

        # Build the query
        # TODO: I need to be using request.get_wfdisc_rows here.
        #q = req.get_wfdisc_rows(self.session, Wfdisc, t1, t2, asquery=True)

        q = self.session.query(Wfdisc)

        q = q.filter(Wfdisc.sta == Affil.sta)

        # apply string filters/expressions
        q = q.filter(util.string_expression(Affil.net, networks))
        q = q.filter(util.string_expression(Wfdisc.sta, stations))
        q = q.filter(util.string_expression(Wfdisc.chan, channels))

        # TODO: time here
        CHUNKSIZE = 24 * 60 * 60
        q = q.filter(Wfdisc.time.between(t1 - CHUNKSIZE, t2))
        q = q.filter(Wfdisc.time > t1)
        q = q.filter(Wfdisc.time <= t2)

        if minimumlength:
            q = q.filter((Wfdisc.endtime - Wfdisc.time ) > minimumlength)

        log.debug(util.literal_sql(self.session, q))

        st = Stream()
        for wf in q:
            try:
                tr = wfdisc2trace(wf)
                st.append(tr)
            except IOError:
                msg = "Unable to read file: dir = {}, dfile = {}"
                log.error(msg.format(wf.dir, wf.dfile)) # TODO: append action IOError message, too

        st.trim(starttime, endtime)
        # TODO: merge them?

        return st
