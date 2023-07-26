"""
Tests for the pisces.request module


"""
from obspy import UTCDateTime
import pytest

from pisces import stations
from pisces.tables.kbcore import *

def test_query_network_nets(session, get_stations_data):
    """ Tests involving network-level queries. """
    d = get_stations_data
    
    # All networks are returned if none specified 
    # expected = [
    #     Network(net='IM'),
    #     Network(net='IU'),
    #     Network(net='SR'),
    # ]
    query = session.query(Network)
    out = stations.filter_networks(query).order_by(Network.net).all()
    assert out == [d['IM'], d['IU'], d['SR']]

    # correct network is returned if provided
    # expected = [
    #     Network(net='IU')
    # ]
    out = stations.filter_networks(query, net=['IU']).all()
    assert out == [d['IU']]

    # Affiliation information is present if provided
    # expected = [
    #     (Network(net='IU'), Affiliation(net='IU', sta='ANMO', time=620352000.0)),
    #     (Network(net='IU'), Affiliation(net='IU', sta='ANMO', time=972000000.0)),
    # ]
    query = query.add_entity(Affiliation)
    q = stations.filter_networks(query, net=['IU'])
    out = q.order_by(Affiliation.time).all()
    assert (
        len(out) == 2 and # two results returned
        len(out[0]) == 2 and # two entities in each result
        out[0] == (d['IU'], d['IU_ANMO_1']) and
        out[1] == (d['IU'], d['IU_ANMO_2'])
    )

def test_query_network_stas(session, get_stations_data):
    """ Tests involving station-level queries. """
    d = get_stations_data

    # only one Network for one specific station is included when stas specified
    # and a station is only associated with one network.
    # expected = [
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV33', time=-9999999999.999))
    # ]
    query = session.query(Network, Affiliation)
    out = stations.filter_networks(query, sta=['NV33']).all()
    assert (
        len(out) == 1 and
        out[0] == (d['IM'], d['IM_NV33'])
    )

    with pytest.raises(NameError):
        # without Affiliation provided, stas should fail
        out = stations.filter_networks(q, sta=['NV33']).all()

    # two Networks for one specific station is included when stas specified
    # and a station is associated with two networks.
    # expected = [
    #     (Network(net='SR'), Affiliation(net='SR', sta='ANMO', time=...)),
    #     (Network(net='IU'), Affiliation(net='IU', sta='ANMO', time=620352000.0)),
    #     (Network(net='IU'), Affiliation(net='IU', sta='ANMO', time=972000000.0)),
    # ]
    q = stations.filter_networks(query, sta=['ANMO'])
    out = q.order_by(Affiliation.time).all()
    assert (
        len(out) == 3 and
        out[0] == (d['SR'], d['SR_ANMO_0']) and
        out[1] == (d['IU'], d['IU_ANMO_1']) and
        out[2] == (d['IU'], d['IU_ANMO_2'])
    )

    # wildcarded array elements are returned properly
    # expected = [
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV32', time=-9999999999.999))
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV33', time=-9999999999.999))
    # ]
    q = stations.filter_networks(query, sta=['NV*'])
    out = q.order_by(Affiliation.sta).all()
    assert (
        len(out) == 2 and
        out[0] == (d['IM'], d['IM_NV32']) and
        out[1] == (d['IM'], d['IM_NV33'])
    )

def test_query_network_time(session, get_stations_data):
    """ Tests involving time-based queries. """
    d = get_stations_data

    # get results where network affiliation ends after time_
    # expected = [
    #     (Network(net='IU'), Affiliation(net='IU', sta='ANMO', time=972000000.0)),
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV32', time=1987200.0)),
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV33', time=-9999999999.999)),
    # ]
    # TODO: Is this how time_ is meant to work?
    times= (UTCDateTime('2001-01-01'), None)
    query = session.query(Network, Affiliation)
    q = stations.filter_networks(query, times=times)
    out = q.order_by(Affiliation.endtime).all()
    assert (
        len(out) == 3 and
        out[0] == (d['IU'], d['IU_ANMO_2']) and
        out[1] == (d['IM'], d['IM_NV32']) and
        out[2] == (d['IM'], d['IM_NV33'])
    )
    with pytest.raises(ValueError):
        # without Affiliation provided, time queries should fail
        query = session.query(Network)
        out = stations.filter_networks(query, times=times).all()
        
    # get results where network affiliation.time < endtime
    # expected = [
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV33', time=-9999999999.999)),
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV32', time=1987200.0)),
    #     (Network(net='SR'), Affiliation(net='SR', sta='ANMO', time=154051200.0)),
    # ]
    times = (None, UTCDateTime('1980-01-01'))
    query = session.query(Network, Affiliation)
    q = stations.filter_networks(query, times=times)
    out = q.order_by(Affiliation.time).all()
    assert (
        len(out) == 3 and
        out[0] == (d['IM'], d['IM_NV33']) and
        out[1] == (d['IM'], d['IM_NV32']) and
        out[2] == (d['SR'], d['SR_ANMO_0'])
    )

    # without Affiliation provided, time queries should fail
    with pytest.raises(ValueError):
        query = session.query(Network)
        out = stations.filter_networks(query, times=times).all()