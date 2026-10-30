"""
Test functions in pisces.util

"""
from configparser import ConfigParser

import pisces.util as util


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
