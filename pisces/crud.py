"""
Module for schema-aware table creation and dropping functions.

"""
import  pisces.tables.css3 as css3
import  pisces.tables.kbcore as kb

def format_table_names(*tables, **kwargs):
    """
    Get a list of table name strings in the format: <owner>.<prefix>table .

    Parameters
    ----------
    tables : iterable of str
        Desired canonical table names.  If omitted, all core tables for the
        schema are used.
    schema : str  ("css3" or "kbcore")
        Which set of core tables are being used.
        Default is "css3".
    prefix : str
        e.g. "TA_" for "TA_origin", "TA_wfdisc", etc.
    owner : str
        e.g. "myuser" for "myuser.origin", "myuser.wfdisc", etc.

    Returns
    -------
    tablenames : dict
        The desired formatted table name strings.

    """
    prefix = kwargs.pop('prefix', '')
    owner = kwargs.pop('owner', None)
    schema = kwargs.pop('schema', 'css3')

    if schema == 'css3':
        CORETABLES = css3.CORETABLES
    elif schema == 'kbcore':
        CORETABLES = kb.CORETABLES
    else:
        raise ValueError("Unknown schema {}".format(schema))

    if not tables:
        tables = CORETABLES.keys()

    tablenames = [

def make_tables(tables=None, schema='kbcore', prefix="", owner=None):
    pass


def load_tables(session, tables=None, schema='kbcore', prefix="", owner=None):
    pass


def init_tables(session, *tables):
    pass


def drop_tables(session, *tables):
    pass
