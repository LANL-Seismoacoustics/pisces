from pisces.query import util

def test_make_wildcard_list():
    assert util.make_wildcard_list('*HZ') == ['%HZ']
    assert util.make_wildcard_list('?HZ') == ['_HZ']
    assert util.make_wildcard_list('*HZ,HHZ') == ['%HZ', 'HHZ']
    assert util.make_wildcard_list(('*HZ', 'HHZ')) == ['%HZ', 'HHZ']
