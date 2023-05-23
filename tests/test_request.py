"""
Tests for the pisces.request module

"""
from obspy import UTCDateTime
import pytest

import pisces.request as req
from pisces.tables.kbcore import *

def test_query_network(session, get_stations_data):
    d = get_stations_data
    
    # All networks are returned if none specified 
    # expected = [
    #     Network(net='IM'),
    #     Network(net='IU'),
    #     Network(net='SR'),
    # ]
    out = req.query_network(session, Network).order_by(Network.net).all()
    assert out == [d['IM'], d['IU'], d['SR']]

    # correct network is returned if provided
    # expected = [
    #     Network(net='IU')
    # ]
    out = req.query_network(session, Network, nets=['IU']).all()
    assert out == [d['IU']]

    # Affiliation information is present if provided
    # expected = [
    #     (Network(net='IU'), Affiliation(net='IU', sta='ANMO', time=620352000.0)),
    #     (Network(net='IU'), Affiliation(net='IU', sta='ANMO', time=972000000.0)),
    # ]
    q = req.query_network(session, Network, nets=['IU'], affiliation=Affiliation)
    out = q.order_by(Affiliation.time).all()
    assert (
        len(out) == 2 and # two results returned
        len(out[0]) == 2 and # two entities in each result
        out[0] == (d['IU'], d['IU_ANMO_1']) and
        out[1] == (d['IU'], d['IU_ANMO_2'])
    )

    # only one Network for one specific station is included when stas specified
    # and a station is only associated with one network.
    # expected = [
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV33', time=-9999999999.999))
    # ]
    out = req.query_network(session, Network, affiliation=Affiliation, stas=['NV33']).all()
    assert (
        len(out) == 1 and
        out[0] == (d['IM'], d['IM_NV33'])
    )

    with pytest.raises(NameError):
        # without Affiliation provided, stas should fail
        out = req.query_network(session, Network, stas=['NV33']).all()

    # two Networks for one specific station is included when stas specified
    # and a station is associated with two networks.
    # expected = [
    #     (Network(net='SR'), Affiliation(net='SR', sta='ANMO', time=...)),
    #     (Network(net='IU'), Affiliation(net='IU', sta='ANMO', time=620352000.0)),
    #     (Network(net='IU'), Affiliation(net='IU', sta='ANMO', time=972000000.0)),
    # ]
    q = req.query_network(session, Network, affiliation=Affiliation, stas=['ANMO'])
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
    q = req.query_network(session, Network, affiliation=Affiliation, stas=['NV*'])
    out = q.order_by(Affiliation.sta).all()
    assert (
        len(out) == 2 and
        out[0] == (d['IM'], d['IM_NV32']) and
        out[1] == (d['IM'], d['IM_NV33'])
    )

    # get results where network affiliation ends after time_
    # expected = [
    #     (Network(net='IU'), Affiliation(net='IU', sta='ANMO', time=972000000.0)),
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV32', time=1987200.0)),
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV33', time=-9999999999.999)),
    # ]
    # TODO: Is this how time_ is meant to work?
    time_= UTCDateTime('2001-01-01') 
    q = req.query_network(session, Network, affiliation=Affiliation, time_=time_)
    out = q.order_by(Affiliation.endtime).all()
    assert (
        len(out) == 3 and
        out[0] == (d['IU'], d['IU_ANMO_2']) and
        out[1] == (d['IM'], d['IM_NV32']) and
        out[2] == (d['IM'], d['IM_NV33'])
    )
    with pytest.raises(NameError):
        # without Affiliation provided, time queries should fail
        out = req.query_network(session, Network, time_=time_).all()
        

    # get results where network affiliation.time < endtime
    # expected = [
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV33', time=-9999999999.999)),
    #     (Network(net='IM'), Affiliation(net='IM', sta='NV32', time=1987200.0)),
    #     (Network(net='SR'), Affiliation(net='SR', sta='ANMO', time=154051200.0)),
    # ]
    endtime = UTCDateTime('1980-01-01')
    q = req.query_network(session, Network, affiliation=Affiliation, endtime=endtime)
    out = q.order_by(Affiliation.time).all()
    assert (
        len(out) == 3 and
        out[0] == (d['IM'], d['IM_NV33']) and
        out[1] == (d['IM'], d['IM_NV32']) and
        out[2] == (d['SR'], d['SR_ANMO_0'])
    )

    # without Affiliation provided, time queries should fail
    with pytest.raises(NameError):
        out = req.query_network(session, Network, endtime=endtime).all()

    # if a query object is provided
    # should append Networks, Affiliations that contain the sta to the result set
    q = session.query(Site).filter(Site.sta.in_(['NV32', 'NV33']))
    q = req.query_network(session, Network, affiliation=Affiliation, with_query=q)
    out = q.order_by(Affiliation.time).all()
    # expected = [
    #     (Site(sta='NV33', ondate=1970024), Affiliation(net='IM', sta='NV33', time=-9999999999.999), Network(net='IM')),
    #     (Site(sta='NV32', ondate=1970024), Affiliation(net='IM', sta='NV32', time=1987200.0), Network(net='IM')),
    #     ]
    assert (
        len(out) == 2 and
        out[0] == (d['NV33'], d['IM_NV33'], d['IM']) and
        out[1] == (d['NV32'], d['IM_NV32'], d['IM'])
    )