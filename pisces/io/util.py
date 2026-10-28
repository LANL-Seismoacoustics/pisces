# Converted to python 3.5.2 on 02/07/17
# By: Jeremy Webster

"""
Common io utilities.

"""
import functools

from pisces.util import deprecated


def _buildhdr(keymap, rec):
    """
    Map attributes in rec into a dictionary, with keyname translations applied.

    Raises
    ------
    AttributeError
        rec does not have attributes (is None?)

    """
    # TODO: make keymap optional?
    # TODO: put this in io.util?
    hdr = {}
    for key1, key2 in keymap.items():
        try:
            hdr[key1] = getattr(rec, key2)
        except AttributeError:
            # rec doesn't have attribute or rec is None. skip
            pass

    return hdr


@deprecated('Unused internally; prefer plain dict comprehensions or the '
            'pisces.io.util cast/strip helpers (_cast_int, _cast_float, _clean_str).')
def _map_header(keymap, dold, nulldict=None):
    """
    Returns a dictionary of values from dictionary dold,
    mapped to new key, if provided.

    Parameters
    ----------
    keymap: dict
        The map between old and new dictionary keys.
        Of the form {oldkey: newkey, ...}
    dold: dict
        The values to hand over.
    nulldict: dict, optional
        Dictionary representing null values in source dictionary.
        Matching values will not be transferred.

    Returns: dict

    """
    # TODO: this confusing function should be rewritten  (using defaultdict?)
    dnew = {}
    if nulldict:
        for oldkey, newkey in keymap.items():
            try:
                if dold[oldkey] != nulldict[oldkey]:
                    if isinstance(dold[oldkey], str):
                        dnew[newkey] = dold[oldkey].strip()
                    else:
                        dnew[newkey] = dold[oldkey]
            except KeyError:
                # one of the dictionaries doesn't have a key
                pass
    else:
        for oldkey, newkey in keymap.items():
            try:
                if isinstance(dold[oldkey], str):
                    dnew[newkey] = dold[oldkey].strip()
                else:
                    dnew[newkey] = dold[oldkey]
            except KeyError:
                pass

    return dnew


def _cast_int(d, keys):
    """In place: cast d[key] to int for each key present and non-None."""
    for key in keys:
        if d.get(key) is not None:
            d[key] = int(d[key])
    return d


def _cast_float(d, keys):
    """In place: cast d[key] to float for each key present and non-None."""
    for key in keys:
        if d.get(key) is not None:
            d[key] = float(d[key])
    return d


def _clean_str(d, keys):
    """In place: strip whitespace from d[key] for each key present and non-None."""
    for key in keys:
        if d.get(key) is not None:
            d[key] = d[key].strip()
    return d


class Registry:
    """ Dictionary-like registry decorator.

    Useful for keeping track of I/O functions for file formats or core schema classes.

    Examples
    --------
    >>> register = Registry()

    >>> @register('miniseed')
    >>> def read_miniseed():
    ...     pass

    >>> 'miniseed' in register
    True
    >>> register['miniseed'] == read_miniseed
    True

    >>> @register('miniseed')
    >>> def read_miniseed2():
    ...     pass

    KeyError: 'key already exists in registry.  use force=True to override it.'

    >>> @register('miniseed', force=True)
    >>> def read_miniseed2():
    ...     pass

    >>> register['miniseed'] == read_miniseed2
    True

    >>> CORETABLES = Registry()
    >>> @CORETABLES('site')
    ... class Site:
    ...     pass

    >>> register['site']
    __main__.Site

    """
    # TODO: inherit/implement collections.abc.Mapping?
    def __init__(self):
        self._REGISTRY = {}

    def __call__(self, key, force=False):
        """ Function decorator that registers using a key.
        """
        def actual_decorator(func):
            if key in self._REGISTRY and not force:
                raise KeyError("key already exists in registry.  use force=True to override it.")
            self._REGISTRY[key] = func

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper

        return actual_decorator

    def __repr__(self):
        return repr(self._REGISTRY)

    def __getitem__(self, key):
        return self._REGISTRY[key]

    def __len__(self):
        return len(self._REGISTRY)

    def __iter__(self):
        for key in self._REGISTRY:
            yield key
