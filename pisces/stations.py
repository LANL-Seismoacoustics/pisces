import numpy as np
from sqlalchemy import func, or_
from obspy.core import UTCDateTime, Stream
import obspy.geodetics as geod

from pisces.io.trace import wfdisc2trace
from pisces.util import make_wildcard_list, _get_entities

import warnings

def filter_network(query, net=None, netname=None, nettype=None, auth=None, sta=None,  time_=None, **tables):
    """ipython
    Parameters
    ----------
    session : sqlalchemy.orm.session instance, bound
    network : 
    nets : 
    affiliation : 
    stas :
    time_ :
    endtime : 
    pref_nets : 
    with_query :
    site_name :  
    Returns
    -------
    query
        sdfs
    
    Notes:
    ------
    If input into get_networks is a query, an affiliation table must be provided and the query must contain a site table to be
    joined on affiliation.sta == site.sta .

    Results cannot be filtered with a station list if affiliation table is not provided.
    """

    # get desired tables from the query
    Network, Affiliation, Site, Sitechan, Sensor = _get_entities(query, "Network", "Affiliation","Site","Sitechan","Sensor")
    # override if provided
    # XXX: add a flag for the 'filter but don't include'
    Network = tables.get("network", None) or Network
    Affiliation = tables.get("affiliation", None) or Affiliation
    Site = tables.get("site", None) or Site
    Sitechan = tables.get("sitechan", None) or Sitechan
    Sensor = tables.get("sensor", None) or Sensor

    # avoid nonsense inputs
    if not any([Network, Affiliation]):
        msg = "Network or Affiliation table required."
        raise ValueError(msg)
    
    if any([netname, nettype, auth]) and not Network:
        # Origin keywords supplied, but no Origin table present
        # TODO: replace with pisces.exc.MissingTableError
        msg = "Network table required."
        raise ValueError(msg)

    if any([sta, time_]) and not Affiliation:
        # Origin keywords supplied, but no Origin table present
        # TODO: replace with pisces.exc.MissingTableError
        msg = "Affiliation table required."
        raise ValueError(msg)
    
    if Network and Affiliation:
        query = query.filter(Network.net == Affiliation.net)

    if Affiliation and Site:
        query = query.filter(Site.sta == Affiliation.sta)
    elif Affiliation and Sitechan:
        query = query.filter(Sitechan.sta == Affiliation.sta)
    elif Affiliation and Sensor:
        query = query.filter(Sensor.sta == Affiliation.sta)

    if net:
        net = make_wildcard_list(net)
        query = query.filter(or_(*[Network.net.like(nets) for nets in net]))
    
    if netname:
        netname = make_wildcard_list(netname)
        query = query.filter(or_(*[Network.netname.like(netnames) for netnames in netname]))
    
    if nettype:
        nettype = make_wildcard_list(nettype)
        query = query.filter(or_(*[Network.nettype.like(nettypes) for nettypes in nettype]))
    
    if auth:
        auth = make_wildcard_list(auth)
        query = query.filter(or_(*[Network.net.like(auths) for auths in auth]))

    if sta:
        sta = make_wildcard_list(sta)
        query = query.filter(or_(*[Affiliation.sta.like(stas) for stas in sta]))

    if time_:
        t1, t2 = time_
        t1 = UTCDateTime(t1).timestamp if t1 else None
        t2 = UTCDateTime(t2).timestamp if t2 else None
        if t1:
            query = query.filter(t1 < Affiliation.endtime)
        if t2:
            query = query.filter(t2 > Affiliation.time)

    return query


def query_site(session, site, sitechan=None, stas=None, chans=None, time_=None, endtime=None, with_query = None):
    """
    Parameters
    ----------
    session : sqlalchemy.orm.session instance, bound
    site : 
    sitechan : 
    stas : 
    chans :
    time_ :
    endtime :  
    with_query :
    affiliation_name :
    sensor_name:

    Returns
    -------
    query
        sdfs
    
    Notes:
    ------
    
    """
    if with_query:

        q = with_query
        
        affiliation = None
        sensor = None

        for i in q.column_descriptions:
            checkEntity = i['entity']
            if checkEntity._tabletype == 'Affiliation':
                affiliation = checkEntity
            if checkEntity._tabletype == 'Sensor':
                sensor = checkEntity
        
        if affiliation and sensor:
            q = q.add_entity(site)
            q = q.join(site, affiliation.sta == site.sta)
            if sitechan:
                q = q.add_entity(sitechan)
                q = q.join(sitechan, site.sta == sitechan.sta)
                q = q.join(sitechan, sitechan.chanid == sensor.chanid)
            else:
                q = q.join(sensor, site.sta == sensor.sta)
                warnings.warn("No sitechan specified, joining site to sensor on column sta")

        elif  affiliation:
            q = q.add_entity(site)
            q = q.join(site, affiliation.sta == site.sta)
            if sitechan:
                q = q.add_entity(sitechan)
                q = q.join(sitechan, site.sta == sitechan.sta)

        elif sensor:
            if sitechan:
                q = q.add_entity(sitechan)
                q = q.join(sitechan, sitechan.chanid == sensor.chanid)
                q = q.add_entity(site)
                q = q.join(site, site.sta == sensor.sta)
            else:
                q = q.add_entity(site)
                q =q.join(site, site.sta == sensor.sta)
                warnings.warn("No sitechan specified, joining site to sensor on column sta")
        else: 
            raise NameError("No affiliation or sensor table in provided in input query for join to site")
         
    else:
        q = session.query(site)
        if sitechan:
            q = q.add_entity(sitechan)
            q = q.join(sitechan, sitechan.sta==site.sta)

    if stas:
        stas = make_wildcard_list(stas)
        q = q.filter(or_(*[site.sta.like(sta) for sta in stas]))

    if chans:
        if not sitechan:
            raise NameError('Sitechan table required to filter site table by channels')
        stations = make_wildcard_list(chans)
        q = q.filter(or_(*[sitechan.chan.like(chan) for chan in chans]))

    if time_:
        jultime_ = int(time_.strftime('%Y%j'))
        q = q.filter(jultime_ < site.offdate)

    if endtime:
        julendtime = int(endtime.strftime('%Y%j'))
        q = q.filter(julendtime > site.ondate)

    return q

def filter_responses(query, sta = None, chan = None, time_ = None):
    """
    Parameters
    ----------
    session : sqlalchemy.orm.session instance, bound
    sensor : 
    instrument : 
    stas : 
    chans :
    time_ :
    endtime :  
    with_query :

    Returns
    -------
    query
        sdfs
    
    Notes:
    ------
    
    """
    # get desired tables from the query
    Affiliation, Site, Sitechan, Sensor, Instrument = _get_entities(query,"Affiliation","Site","Sitechan","Sensor", "Instrument")
    # override if provided
    # XXX: add a flag for the 'filter but don't include'
    Affiliation = tables.get("affiliation", None) or Affiliation
    Site = tables.get("site", None) or Site
    Sitechan = tables.get("sitechan", None) or Sitechan
    Sensor = tables.get("sensor", None) or Sensor
    Instrument = tables.get("instrument", None) or Instrument

    # avoid nonsense inputs
    if not Sensor and Instrument:
        msg = "Sensor and Instrument table required."
        raise ValueError(msg)

    query = query.filter(Sensor.inid == Instrument.inid)

    if Sitechan:
        query = query.filter(Sitechan.chanid == Sensor.chanid)
    elif Site:
        query = query.filter(Sensor.sta == Site.sta)
    elif Affiliation:
        query = query.filter(Sensor.sta == Affiliation.sta)

    if sta:
        sta = make_wildcard_list(sta)
        q = q.filter(or_(*[sensor.sta.like(stas) for stas in sta]))

    if chan:
        chan = make_wildcard_list(chan)
        q = q.filter(or_(*[sensor.chan.like(chans) for chans in chan]))
# copy filter network logic here
    if time_:
        q = q.filter(time_.timestamp < sensor.endtime)

    if endtime:
        q = q.filter(endtime.timestamp > sensor.time)


    return q

def assign_unique_net(q, network_name, affiliation_name, pref_nets = None, two_char_code = True, first_available = True, default_net = '__'):
    return 

def check_orphan_stas():
    return
