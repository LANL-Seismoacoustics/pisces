"""
Test functions in pisces.util

"""
from configparser import ConfigParser
import datetime

import pytest

import sqlalchemy as sa
from obspy import UTCDateTime

import pisces.util as util
from pisces.tables.css3 import Sitechan


@pytest.mark.skip(reason="FDSNClient tests")
def test_datetime_to_epoch():
    epoch = 1504904052.687516

    dt = datetime.datetime.fromtimestamp(epoch)
    assert util.datetime_to_epoch(dt) == pytest.approx(epoch)

    utc = UTCDateTime(epoch)
    assert util.datetime_to_epoch(utc) == pytest.approx(epoch)

@pytest.mark.skip(reason="FDSNClient tests")
def test_glob_to_like():
    assert util.glob_to_like('BH*') == 'BH%'
    assert util.glob_to_like('BH?') == 'BH_'
    assert util.glob_to_like('BH%') == 'BH\\%'

@pytest.mark.skip(reason="FDSNClient tests")
def test_has_sql_wildcards():
    assert util.has_sql_wildcards('_HZ')
    assert util.has_sql_wildcards('%HZ')
    assert not util.has_sql_wildcards('\\_HZ')
    assert not util.has_sql_wildcards('\\%HZ')
    assert not util.has_sql_wildcards('*HZ')
    assert not util.has_sql_wildcards('?HZ')

def test_make_wildcard_list():
    assert util.make_wildcard_list('*HZ') == ['%HZ']
    assert util.make_wildcard_list('?HZ') == ['_HZ']
    assert util.make_wildcard_list('*HZ,HHZ') == ['%HZ', 'HHZ']
    assert util.make_wildcard_list(('*HZ', 'HHZ')) == ['%HZ', 'HHZ']

@pytest.mark.skip(reason="FDSNClient tests")
def test_string_expressions():
    expression = util.string_expression(Sitechan.chan, ['BHZ'])
    assert expression == (Sitechan.chan == 'BHZ')

    channels = ['BHZ', 'BHN']
    expression = util.string_expression(Sitechan.chan, channels)
    assert expression == sa.or_(Sitechan.chan.in_(channels))

    expression = util.string_expression(Sitechan.chan, ['BH%'])
    assert expression == Sitechan.chan.like('BH%')

    channels = ['BHZ', 'LH%']
    expression = util.string_expression(Sitechan.chan, channels)
    assert expression == sa.or_(Sitechan.chan == 'BHZ',
                                Sitechan.chan.like('LH%'))


def test_load_config_file():
    CFG = """
    [database]
    url = sqlite:///mydb.sqlite
    """
    config = ConfigParser()
    config.read_string(CFG)
    session, tables = util.load_config(config['database'])
    assert str(session.bind.url) == 'sqlite:///mydb.sqlite'
    assert tables == {}

def test_load_config_dict():
    config = {'url': 'sqlite:///mydb.sqlite'}
    session, tables = util.load_config(config)
    assert str(session.bind.url) == 'sqlite:///mydb.sqlite'
    assert tables == {}

