import  pisces.schema.kbcore as kb
import  pisces.schema.kbcore as css3

def format_table_names(tables=None, prefix="", owner=None, schema='css3'):
    """
    Get a list of table name strings in the format: <owner>.<prefix>table .

    Parameters
    ----------
    tables : iterable of str
        Desired canonical table names.  If omitted, all core tables for the
        schema are used.
    prefix : str
        e.g. "TA_" for "TA_origin", "TA_wfdisc", etc.
    owner : str
        e.g. "myuser" for "myuser.origin", "myuser.wfdisc", etc.
    schema : str
        Which set of core tables are being used. "css3" or "kbcore"
    exclude : iterable of str
        Canonical table name strings to exclude.  This is applied _after_ the
        `tables` parameter.

    Returns
    -------
    tablenames : dict
        The desired formatted table name strings.

    """
    prefix = kwargs.pop('prefix', '')
    owner = kwargs.pop('owner', None)
    schema = kwargs.pop('schema', 'css3')


def make_tables(tables=None, schema='kbcore', prefix="", owner=None):
    pass


def load_tables(session, tables=None, schema='kbcore', prefix="", owner=None):
    pass


def init_tables(session, *tables):
    pass

def drop_tables(session, *tables):
    pass
