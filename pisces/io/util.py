# Converted to python 3.5.2 on 02/07/17
# By: Jeremy Webster

"""
Common io utilities.

"""
import functools


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



from collections.abc import Mapping

class Registry2(Mapping):
    """ Dictionary-like registry decorator.

    Useful for keeping track of I/O functions for file formats or core schema classes.

    Examples
    --------
    >>> formats = Registry()

    >>> @formats.register('miniseed')
    >>> def read_miniseed():
    ...     pass

    >>> 'miniseed' in formats
    True
    >>> formats['miniseed'] == read_miniseed
    True

    >>> @formats('miniseed')
    >>> def read_miniseed2():
    ...     pass

    KeyError: 'key already exists in registry.  use force=True to override it.'

    >>> @formats('miniseed', force=True)
    >>> def read_miniseed2():
    ...     pass

    >>> formats['miniseed'] == read_miniseed2
    True

    >>> CORETABLES = Registry()
    >>> @CORETABLES.register('site')
    ... class Site:
    ...     pass

    >>> CORETABLES['site']
    __main__.Site

    # existing functions or classes can also be registered using inline decorator syntax
    >>> from mytables import MyTable
    >>> MyTable = CORETABLES.register('mytable')(MyTable)

    """
    # hijack normal Mapping init to initialize registry
    def __init__(self, *args, **kwargs):
        self._REGISTRY = dict(*args, **kwargs)

    def __repr__(self):
        return repr(self._REGISTRY)

    def register(self, key, force=False):
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

    def __getitem__(self, key):
        return self._REGISTRY[key]

    def __len__(self):
        return len(self._REGISTRY)

    def __iter__(self):
        for key in self._REGISTRY:
            yield key
