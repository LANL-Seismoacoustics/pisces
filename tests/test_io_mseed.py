"""
Tests for pisces.io.mseed trace<->table conversions.

"""
from obspy import Trace
import numpy as np

import pisces.io.mseed as mseed


def make_trace(**stats):
    """Build a Trace with the given stats fields set, 10 zero samples."""
    tr = Trace(data=np.zeros(10, dtype='float32'))
    for key, value in stats.items():
        setattr(tr.stats, key, value)
    return tr


def test_trace2tables_full_header():
    """A Trace with network/station/channel/calib set converts to correct
    site, sitechan, affiliation, and wfdisc rows.
    """
    tr = make_trace(network='XX', station='STA', channel='BHZ',
                     sampling_rate=100.0, calib=2.0)
    rows = mseed.trace2tables(tr)

    assert rows['site'] == [{'sta': 'STA'}]
    assert rows['sitechan'] == [{'sta': 'STA', 'chan': 'BHZ'}]
    assert rows['affiliation'] == [{'net': 'XX', 'sta': 'STA'}]

    wfdisc = rows['wfdisc'][0]
    assert wfdisc['sta'] == 'STA'
    assert wfdisc['chan'] == 'BHZ'
    assert wfdisc['nsamp'] == 10
    assert wfdisc['samprate'] == 100.0
    assert wfdisc['calib'] == 2.0
    assert wfdisc['datatype'] == 'sd'
    assert wfdisc['time'] == tr.stats.starttime.timestamp
    assert wfdisc['endtime'] == tr.stats.endtime.timestamp


def test_trace2tables_minimal_header_omits_empty_tables():
    """A Trace with no network/station/channel set only produces a wfdisc
    row (always present); site/sitechan/affiliation are omitted since their
    identifying fields are empty.
    """
    tr = make_trace()
    rows = mseed.trace2tables(tr)

    assert set(rows) == {'wfdisc'}
    assert rows['wfdisc'][0]['nsamp'] == 10


def test_trace2tables_tables_filter():
    """The `tables` argument restricts trace2tables' output to only the
    requested canonical table names.
    """
    tr = make_trace(station='STA')
    rows = mseed.trace2tables(tr, tables=['site'])
    assert set(rows) == {'site'}
