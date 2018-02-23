"""
Test functions in pisces.util.py

"""
from configparser import ConfigParser

from pisces.util import load_config

def test_load_config_file():
    CFG = """
    [database]
    url = sqlite:///mydb.sqlite
    """
    config = ConfigParser()
    config.read_string(CFG)
    session, tables = load_config(config['database'])
    assert (session.bind.url) == 'sqlite:///mydb.sqlite'
    assert tables == {}

def test_load_config_dict():
    config = {'url': 'sqlite:///mydb.sqlite'}
    session, tables = load_config(config)
    assert (session.bind.url) == 'sqlite:///mydb.sqlite'
    assert tables == {}