"""
Tests for pisces.io.util helpers.

"""
from types import SimpleNamespace

from pisces.io.util import _buildhdr


def test_buildhdr_keymap():
    """_buildhdr maps attributes off `rec` into a dict under new key names,
    per `keymap` ({new_key: rec_attr}), skipping any rec attr that's missing.
    """
    rec = SimpleNamespace(npts=100, chan='BHZ')
    keymap = {'nsamp': 'npts', 'channel': 'chan', 'missing': 'nope'}

    hdr = _buildhdr(keymap, rec)

    assert hdr == {'nsamp': 100, 'channel': 'BHZ'}


def test_buildhdr_none_rec():
    """_buildhdr returns an empty dict, rather than raising, when `rec` is
    None (e.g. a missing/optional table row).
    """
    hdr = _buildhdr({'nsamp': 'npts'}, None)

    assert hdr == {}
