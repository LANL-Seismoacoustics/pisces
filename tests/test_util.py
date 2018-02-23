"""
Test functions in pisces.util

"""
from configparser import ConfigParser
import datetime
import unittest

import sqlalchemy as sa
from obspy import UTCDateTime

import pisces.util as util
from pisces.util import load_config
from pisces.tables.css3 import Sitechan

class TestUtils(unittest.TestCase):
    def test_datetime_to_epoch(self):
        epoch = 1504904052.687516
        dt = datetime.datetime.fromtimestamp(epoch)
        self.assertAlmostEqual(util.datetime_to_epoch(dt), epoch)
        utc = UTCDateTime(epoch)
        self.assertAlmostEqual(util.datetime_to_epoch(utc), epoch)

    def test_glob_to_like(self):
        self.assertEqual(util.glob_to_like('BH*'), 'BH%')
        self.assertEqual(util.glob_to_like('BH?'), 'BH_')
        self.assertEqual(util.glob_to_like('BH%'), 'BH\\%')

    def test_has_sql_wildcards(self):
        self.assertTrue(util.has_sql_wildcards('_HZ'))
        self.assertTrue(util.has_sql_wildcards('%HZ'))
        self.assertFalse(util.has_sql_wildcards('\\_HZ'))
        self.assertFalse(util.has_sql_wildcards('\\%HZ'))
        self.assertFalse(util.has_sql_wildcards('*HZ'))
        self.assertFalse(util.has_sql_wildcards('?HZ'))

    def test_string_expressions(self):
        expression = util.string_expression(Sitechan.chan, ['BHZ'])
        self.assertEqual(expression, Sitechan.chan == 'BHZ')

        channels = ['BHZ', 'BHN']
        expression = util.string_expression(Sitechan.chan, channels)
        self.assertEqual(expression, sa.or_(Sitechan.chan.in_(channels)))

        expression = util.string_expression(Sitechan.chan, ['BH%'])
        self.assertEqual(expression, Sitechan.chan.like('BH%'))

        channels = ['BHZ', 'LH%']
        expression = util.string_expression(Sitechan.chan, channels)
        self.assertEqual(expression, sa.or_(Sitechan.chan == 'BHZ',
                                            Sitechan.chan.like('LH%')))


def test_load_config_file():
    CFG = """
    [database]
    url = sqlite:///mydb.sqlite
    """
    config = ConfigParser()
    config.read_string(CFG)
    session, tables = util.load_config(config['database'])
    assert (session.bind.url) == 'sqlite:///mydb.sqlite'
    assert tables == {}

def test_load_config_dict():
    config = {'url': 'sqlite:///mydb.sqlite'}
    session, tables = util.load_config(config)
    assert (session.bind.url) == 'sqlite:///mydb.sqlite'
    assert tables == {}

if __name__ == '__main__':
    unittest.main()
