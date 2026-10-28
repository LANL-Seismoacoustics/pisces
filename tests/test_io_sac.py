"""
Tests for pisces.io.sac trace<->table conversions.

"""
import numpy as np
import pytest
from obspy.io.sac import SACTrace

import pisces.io.sac as sac


def make_sac_trace(**kwargs):
    """Build an ObsPy Trace carrying a SAC header (trace.stats.sac), like
    what obspy.read(path, format='SAC') would produce.

    """
    kwargs.setdefault('nzyear', 2020)
    kwargs.setdefault('nzjday', 5)
    kwargs.setdefault('nzhour', 1)
    kwargs.setdefault('nzmin', 2)
    kwargs.setdefault('nzsec', 3)
    kwargs.setdefault('nzmsec', 400)
    kwargs.setdefault('delta', 0.01)
    kwargs.setdefault('data', np.zeros(100, dtype='float32'))
    return SACTrace(**kwargs).to_obspy_trace()


def test_trace2tables_full_header():
    """A fully-populated SAC header converts to correct site, sitechan,
    affiliation, event, origin, arrival, assoc, and wfdisc rows, including
    etype/magnitude-type mapping, origin/arrival/assoc time math relative to
    reftime, and t0/kt0 pick-to-phase mapping.
    """
    tr = make_sac_trace(
        kstnm='STA', kcmpnm='BHZ', knetwk='XX',
        stla=10.0, stlo=20.0, stel=100.0,
        cmpaz=0.0, cmpinc=0.0, stdp=5.0,
        evla=1.0, evlo=2.0, evdp=33.0, mag=4.5, imagtyp='imb',
        ievtyp='iquake', iztype='io', o=5.0, nevid=100, norid=200,
        kt0='P', t0=12.3,
        scale=1.0, nwfid=55,
    )
    rows = sac.trace2tables(tr)

    assert rows['site'] == [{'sta': 'STA', 'lat': 10.0, 'lon': 20.0, 'elev': 0.1}]
    assert rows['sitechan'] == [{'sta': 'STA', 'chan': 'BHZ', 'hang': 0.0,
                                  'vang': 0.0, 'edepth': 0.005}]
    assert rows['affiliation'] == [{'net': 'XX', 'sta': 'STA'}]
    assert rows['event'] == [{'evid': 100}]

    origin = rows['origin'][0]
    assert origin['lat'] == 1.0
    assert origin['lon'] == 2.0
    assert origin['depth'] == 0.033
    assert origin['etype'] == 'qt'
    assert origin['mb'] == 4.5
    assert origin['evid'] == 100
    assert origin['orid'] == 200
    # iztype='io' -> origin time is reftime + o
    reftime = SACTrace.from_obspy_trace(tr).reftime
    assert origin['time'] == pytest.approx((reftime + 5.0).timestamp)

    assert len(rows['arrival']) == 1
    arrival = rows['arrival'][0]
    assert arrival['sta'] == 'STA'
    assert arrival['chan'] == 'BHZ'
    assert arrival['iphase'] == 'P'
    assert arrival['time'] == pytest.approx((reftime + 12.3).timestamp)

    assert len(rows['assoc']) == 1
    assoc = rows['assoc'][0]
    assert assoc['sta'] == 'STA'
    assert assoc['orid'] == 200
    assert assoc['phase'] == 'P'

    wfdisc = rows['wfdisc'][0]
    assert wfdisc['sta'] == 'STA'
    assert wfdisc['chan'] == 'BHZ'
    assert wfdisc['nsamp'] == 100
    assert wfdisc['calib'] == 1.0
    assert wfdisc['wfid'] == 55


def test_trace2tables_minimal_header():
    """A SAC header with no station/event fields set only produces
    'instrument' and 'wfdisc' rows (the only tables with always-available
    values: sample rate and npts); all other tables are omitted entirely.
    """
    tr = make_sac_trace()
    rows = sac.trace2tables(tr)

    # only tables with a value-bearing field (samprate/npts) are present
    assert set(rows) == {'instrument', 'wfdisc'}
    assert rows['wfdisc'][0]['nsamp'] == 100
    assert 'sta' not in rows['wfdisc'][0]


def test_trace2origin_needs_iztype():
    """Origin time/jdate are only set when the SAC header's iztype marks the
    reference time as an origin time ('io'); otherwise they're left unset,
    even if event location (evla/evlo) is present.
    """
    # iztype left at the SACTrace default ('ib'), not 'io': no origin time
    tr = make_sac_trace(evla=1.0, evlo=2.0)
    rows = sac.trace2tables(tr, tables=['origin'])
    assert 'time' not in rows['origin'][0]
    assert 'jdate' not in rows['origin'][0]


def test_trace2tables_tables_filter():
    """The `tables` argument restricts trace2tables' output to only the
    requested canonical table names.
    """
    tr = make_sac_trace(kstnm='STA', stla=1.0, stlo=2.0)
    rows = sac.trace2tables(tr, tables=['site'])
    assert set(rows) == {'site'}
