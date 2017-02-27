"""
Common io utilities.

"""

def _buildhdr(keymap, rec):
    """
    Map attributes in rec into a dictionary, with keyname translations applied.

    Raises
    ------
    AttributeError
        rec does not have attributes (is None?)

    """
    #TODO: make keymap optional?
    hdr = {}
    for key1, key2 in keymap.iteritems():
        try:
            hdr[key1] = getattr(rec, key2)
        except AttributeError:
            #rec doesn't have attribute or rec is None. skip
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
    #TODO: this confusing function should be rewritten  (using defaultdict?)
    dnew = {}
    if nulldict:
        for oldkey, newkey in keymap.iteritems():
            try:
                if dold[oldkey] != nulldict[oldkey]:
                    if isinstance(dold[oldkey], str):
                        dnew[newkey] = dold[oldkey].strip()
                    else:
                        dnew[newkey] = dold[oldkey]
            except KeyError:
                #one of the dictionaries doesn't have a key
                pass
    else:
        for oldkey, newkey in keymap.iteritems():
            try:
                if isinstance(dold[oldkey], str):
                    dnew[newkey] = dold[oldkey].strip()
                else:
                    dnew[newkey] = dold[oldkey]
            except KeyError:
                pass

    return dnew

