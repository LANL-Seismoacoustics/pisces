"""
Module for schema-aware table creation and dropping functions.

"""
import  pisces.tables.css3 as css3
import  pisces.tables.kbcore as kb

def format_table_names(*tablenames, **kwargs):
    """
    Get table name strings in the format: <owner.><prefix>tablename.

    Parameters
    ----------
    tablenames : str
        Desired table names.  If omitted, a schema must be specified, and all
        core tables for the schema are returned.
    schema : str  ("css3" or "kbcore")
        Which set of core tables are being used.
    prefix : str
        All table names will have the provided prefix.
        e.g. "TA_" for "TA_origin", "TA_wfdisc", etc.
    owner : str
        e.g. "myuser" for "myuser.origin", "myuser.wfdisc", etc.

    Returns
    -------
    formatted_tablenames : dict
        The desired formatted table name strings.

    Raises
    ------
    ValueError : unknown schema specified, or tablenames omitted and schema
                 not specified

    """
    prefix = kwargs.pop('prefix', '')
    owner = kwargs.pop('owner', None)
    schema = kwargs.pop('schema', None)

    if not tablenames:
        if schema == 'css3':
            CORETABLES = css3.CORETABLES
        elif schema == 'kbcore':
            CORETABLES = kb.CORETABLES
        else:
            msg = "Unknown schema: {}".format(schema)
            raise ValueError(msg)

        tablenames = CORETABLES.keys()

    if owner:
        fmt = "{owner}.{prefix}{tablename}"
    else:
        fmt = "{prefix}{tablename}"

    formatted_tablenames = {}
    for tablename in tablenames:
        formatted_tablenames[tablename] = fmt.format(owner=owner, prefix=prefix,
                                                     tablename=tablename)

    return formatted_tablenames


def make_tables(*tables, schema=None, prefix="", owner=None):
    pass


def load_tables(session, *tables, schema=None, prefix="", owner=None):
    pass


def init_tables(session, *tables):
    pass


def drop_tables(session, *tables):
    pass
