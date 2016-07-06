from itertools import izip_longest
import sqlalchemy as sa
from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import Session

import pisces as ps
import pisces.request as req
from pisces.io.trace import wfdisc2trace


class Client(object):
    """
    Basic database request client.

    """
    def __init__(self, **kwargs):
        """ 
        Initialize a database connection. 

        Parameters
        ----------
        backend: string, optional
            One of the SQLAlchemy connection strings from 
            http://docs.sqlalchemy.org/en/rel_0_7/core/engines.html#database-urls
        user: string, optional
            Not required for sqlite.
        psswd: string, optional
            Not needed for sqlite. Prompted if needed and not provided.
        server: string, optional
            Database host server.
        port: string or integer, optional
            Port on remote server.
        instance: string, optional
            For sqlite, this is the database file name.
        conn: string, optional
            A fully-formed SQLAlchemy style connection string.
        session : sqlalchemy.orm.Session
            An existing session instance.

        Examples
        --------
        >>> from pisces.client import Client
        >>> client = Client(user='scott', backend='oracle', 
                            server='my.server.edu', port=1521, 
                            instance='mydb')

        """
        if kwargs.get('session', None):
            session = session
        else:
            session = ps.db_connect(**kwargs)
        self.metadata = sa.MetaData(session.bind)
        self.session = session

        self.tables = {}

        # do ID management in this class also?

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


    def get_arrivals(self, stations=None, channels=None, atime=None, 
            phases=None, arids=None, orids=None, auth=None):
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

        """
        wfdisc = self.tables.get('wfdisc')
        st = get_waveforms(self.session, wfdisc, station=station, 
                           channel=channel, starttime=starttime, 
                           endtime=endtime, wfids=wfids)

        return st
