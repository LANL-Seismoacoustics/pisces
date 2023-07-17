import numpy as np
from sqlalchemy import func, or_
from obspy.core import UTCDateTime, Stream
import obspy.geodetics as geod

from pisces.io.trace import wfdisc2trace
from pisces.util import make_wildcard_list, _get_entities

import warnings

def filter_network(query, net=None, netname=None, auth=None, sta=None,  time_=None, **tables):
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
    
    if any([netname, auth]) and not Network:
        # Network keywords supplied, but no Network table present
        # TODO: replace with pisces.exc.MissingTableError
        msg = "Network table required."
        raise ValueError(msg)

    if any([sta, time_]) and not Affiliation:
        # Affiliation keywords supplied, but no Affiliation table present
        # TODO: replace with pisces.exc.MissingTableError
        msg = "Affiliation table required."
        raise ValueError(msg)
    
    # join Network and Affiliation if both present
    if Network and Affiliation:
        query = query.filter(Network.net == Affiliation.net)

    # if query contains Site, Sitechan, or Sensor, append to Affiliation 
    # in order of Site, else Sitechan, else Sensor
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
            query = query.filter(t1 <= Affiliation.endtime)
        if t2:
            query = query.filter(t2 >= Affiliation.time)

    return query


def filter_site(query, sta=None, chan=None, time_=None, staname = None, refsta = None, **tables):
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
     # get desired tables from the query
    Site, Sitechan, Sensor, Affiliation = _get_entities(query, "Site","Sitechan","Sensor","Affiliation")
    # override if provided
    # XXX: add a flag for the 'filter but don't include'
    Affiliation = tables.get("affiliation", None) or Affiliation
    Site = tables.get("site", None) or Site
    Sitechan = tables.get("sitechan", None) or Sitechan
    Sensor = tables.get("sensor", None) or Sensor

    if not any([Site, Sitechan]):
        msg = "Site or Sitechan table required."
        raise ValueError(msg)

    if any([staname, refsta]) and not Site:
        # Site keywords supplied, but no Site table present
        # TODO: replace with pisces.exc.MissingTableError
        msg = "Site table required."
        raise ValueError(msg)

    if any([chan]) and not Sitechan:
        # Sitechan keywords supplied, but no Sitechan table present
        # TODO: replace with pisces.exc.MissingTableError
        msg = "Sitechan table required."
        raise ValueError(msg)
    
    # Join Ste and Sitechan if both present
    if Site and Sitechan:
        query = query.filter(Site.sta == Sitechan.sta)
    
    # If Sensor is present join first on Sitechan.chanid if Sitechan present
    # Else join on Site.sta
    if Sensor:
        if Sitechan:
            query = query.filter(Sitechan.chanid == Sensor.chanid)
        else:
            query = query.filter(Sensor.sta == Site.sta)

    # If Affiliation is present join first on Site.sta if Site present
    # Else join on Sitechan.sta 
    if Affiliation:
        if Site:
            query = query.filter(Site.sta == Affiliation.sta)
        else:
            query =query.filter(Sitechan.sta == Affiliation.sta)

    if sta:
        sta = make_wildcard_list(sta)
        if Site:
            query = query.filter(or_(*[Site.sta.like(stas) for stas in sta]))
        else:
            query = query.filter(or_(*[Sitechan.sta.like(stas) for stas in sta]))
    
    if chan:
        chan = make_wildcard_list(chan)
        query = query.filter(or_(*[Sitechan.chan.like(chans) for chans in chan]))


    # Filter by ondate and offdate which are year and julian day represented as integers
    if time_:
        t1, t2 = time_
        t1 = int(UTCDateTime(t1).strftime('%Y%j')) if t1 else None
        t2 = int(UTCDateTime(t2).strftime('%Y%j')) if t2 else None
        
        # If Sitechan is present filter there and the join Sitechan to Site based 
        # on ondate, otherwise channels will be joined on Site ranges where channels 
        # may not actually exist.  If not Sitechan, filter on Site
        if Sitechan:
            if t1:
                query = query.filter(t1 <= Sitechan.offdate)
            if t2: 
                query = query.filter(t1 >= Sitechan.ondate)
            if Sitechan and Site:
                query =query.filter(Sitechan.ondate.between(Site.ondate, Site.offdate))
        else:
            if t1:
                query = query.filter(t1 <= Site.offdate)
            if t2: 
                query = query.filter(t1 >= Site.ondate)
    
    if staname:
        staname = make_wildcard_list(staname)
        query = query.filter(or_(*[Site.staname.like(stanames) for stanames in staname]))
    
    if refsta:
        refsta = make_wildcard_list(refsta)
        query = query.filter(or_(*[Site.refsta.like(refstas) for refstas in refsta]))

    return query

def filter_responses(query, sta = None, chan = None, time_ = None, **tables):
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

    # Join Sensor and Instrument since both are always required for responses 
    query = query.filter(Sensor.inid == Instrument.inid)

    # If Sitechan, Site, or Affiliation are present join first on Sitechan.chanid
    # Then try to join on Site.sta, then try to join on Affiliation.sta
    if Sitechan:
        query = query.filter(Sitechan.chanid == Sensor.chanid)
    elif Site:
        query = query.filter(Sensor.sta == Site.sta)
    elif Affiliation:
        query = query.filter(Sensor.sta == Affiliation.sta)

    if sta:
        sta = make_wildcard_list(sta)
        query = query.filter(or_(*[Sensor.sta.like(stas) for stas in sta]))

    if chan:
        chan = make_wildcard_list(chan)
        query = query.filter(or_(*[Sensor.chan.like(chans) for chans in chan]))

    if time_:
        t1, t2 = time_
        t1 = UTCDateTime(t1).timestamp if t1 else None
        t2 = UTCDateTime(t2).timestamp if t2 else None
        if t1:
            query = query.filter(t1 <= Sensor.endtime)
        if t2:
            query = query.filter(t2 >= Sensor.time)

    return query

def assign_unique_net(q, network_name, affiliation_name, pref_nets = None, two_char_code = True, first_available = True, default_net = '__'):
    return 

def check_orphan_stas():
    return
