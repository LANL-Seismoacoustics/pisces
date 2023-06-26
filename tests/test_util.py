"""
Test functions in pisces.util

"""
from configparser import ConfigParser

import sqlalchemy as sa

import pisces.util as util
from pisces.tables.kbcore import *
from pisces import events


def test_glob_to_like():
    assert util.glob_to_like('BH*') == 'BH%'
    assert util.glob_to_like('BH?') == 'BH_'
    assert util.glob_to_like('BH%') == 'BH\\%'

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


def test_string_expressions():
    expression = util.string_expression(Sitechan.chan, ['BHZ'])
    expected = Sitechan.chan == 'BHZ'
    assert str(expression) == str(expected)

    channels = ['BHZ', 'BHN']
    expression = util.string_expression(Sitechan.chan, channels)
    expected = sa.or_(Sitechan.chan.in_(channels))
    assert str(expression) == str(expected)

    channels = 'BHZ,BHN'
    expression = util.string_expression(Sitechan.chan, channels)
    expected = sa.or_(Sitechan.chan.in_(channels.split(',')))
    assert str(expression) == str(expected)

    expression = util.string_expression(Sitechan.chan, ['BH%'])
    expected = Sitechan.chan.like('BH%')
    assert str(expression) == str(expected)

    expression = util.string_expression(Sitechan.chan, 'BH%')
    expected = Sitechan.chan.like('BH%')
    assert str(expression) == str(expected)

    channels = ['BHZ', 'LH%']
    expression = util.string_expression(Sitechan.chan, channels)
    expected = sa.or_(Sitechan.chan == 'BHZ', Sitechan.chan.like('LH%'))
    assert str(expression) == str(expected)


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

def test_range_filters():
    # empty values produces no filters, just an empty list
    assert events.range_filters((Site.lat, None, None)) == []

    # min value
    # don't know how to test equivalence of column expressions, so we test using their rendered SQL
    observed = events.range_filters((Site.lat, 20, None))
    expected = [Site.lat >= 20]
    assert (
        len(observed) == 1 and
        observed[0].compare(expected[0])
    )

    # max value
    observed = events.range_filters((Site.lat, None, 20))
    expected = [Site.lat <= 20]
    assert (
        len(observed) == 1 and
        observed[0].compare(expected[0])
    )

    # between values
    observed = events.range_filters((Site.lat, 20, 30))
    expected = [Site.lat.between(20, 30)]
    assert (
        len(observed) == 1 and
        observed[0].compare(expected[0])
    )

    # multiple restrictions
    observed = events.range_filters((Site.lat, 20, 30), (Site.lon, None, 42))
    expected = [Site.lat.between(20, 30), Site.lon <= 42]
    assert (
        len(observed) == 2 and
        observed[0].compare(expected[0]) and
        observed[1].compare(expected[1])
    )
