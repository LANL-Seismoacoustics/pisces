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
    Network, Affiliation = _get_entities(query, "Network", "Affiliation")
    # override if provided
    # XXX: add a flag for the 'filter but don't include'
    Network = tables.get("network", None) or Network
    Affiliation = tables.get("affiliation", None) or Affiliation

    # avoid nonsense inputs
    if not any([Network, Affiliation]):
        msg = "Network or Affiliation table required."
        raise ValueError(msg)
    
    if any([netname, nettype, auth]) and not Network:
        # Origin keywords supplied, but no Origin table present
        # TODO: replace with pisces.exc.MissingTableError
        msg = "Network table required."
        raise ValueError(msg)

    if any([sta, time_, endtime]) and not Affiliation:
        # Origin keywords supplied, but no Origin table present
        # TODO: replace with pisces.exc.MissingTableError
        msg = "Affiliation table required."
        raise ValueError(msg)
    
    if Network and Affiliation:
        query = query.filter(Network.net == Affiliation.net)

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
        
        query = query.filter(time_.timestamp < Affiliation.endtime)

    if endtime:
        query = query.filter(endtime.timestamp > Affiliation.time)

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

    if with_query:
        q = with_query

        sitechan = None
        site = None
        affiliation = None

        for i in q.column_descriptions:
            checkEntity = i['entity']
            if checkEntity._tabletype == 'Sitechan':
                sitechan = checkEntity
            if checkEntity._tabletype == 'Site':
                site = checkEntity
            if checkEntity._tabletype == 'Affiliation':
                affiliation = checkEntity
        
        if sitechan:
            q = q.add_entity(sensor)
            q = q.join(sensor, sitechan.chanid == sensor.chanid)

        elif site:
            q = q.add_entity(sensor)
            q = q.join(sensor, sensor.sta == site.sta)
            warnings.warn("No sitechan specified, joining sensor to site on column sta")
        
        elif affiliation:
            q = q.add_entity(sensor)
            q = q.join(sensor, sensor.sta == affiliation.sta)
            warnings.warn("No site or sitechan specified, joining sensor to affiliation on column sta")
        
        else:
            raise NameError("No table in provided query on which to join the sensor table ")

    else:
        q = session.query(sensor)
    
    if instrument:
        q = q.add_entity(instrument)
        q = q.join(instrument, sensor.inid == instrument.inid)

    if stas:
        stas = make_wildcard_list(stas)
        q = q.filter(or_(*[sensor.sta.like(sta) for sta in stas]))

    if chans:
        chans = make_wildcard_list(chans)
        q = q.filter(or_(*[sensor.chan.like(chan) for chan in chans]))

    if time_:
        q = q.filter(time_.timestamp < sensor.endtime)

    if endtime:
        q = q.filter(endtime.timestamp > sensor.time)


    return q

def assign_unique_net(q, network_name, affiliation_name, pref_nets = None, two_char_code = True, first_available = True, default_net = '__'):
    return 

def check_orphan_stas():
    return
