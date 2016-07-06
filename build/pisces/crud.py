"""
Module for schema-aware table creation and dropping functions.

"""
import  pisces.tables.css3 as css3
import  pisces.tables.kbcore as kb

def make_table_names(*tables, **kwargs):
    """
    Get table name strings in the format: <owner.><prefix>tablename.

    Parameters
    ----------
    tables : str
        Desired table names.  If omitted, a schema must be specified, and all
        core tables for the schema are returned.
    schema : str  ("css3" or "kbcore")
        Which set of core tables are being used. If omitted, tables must be
        specified.
    prefix : str
        All table names will have the provided prefix.
        e.g. "TA_" for "TA_origin", "TA_wfdisc", etc.
    owner : str
        e.g. "myuser" for "myuser.origin", "myuser.wfdisc", etc.

    Returns
    -------
    tablenames : tuple 
        The desired formatted table name strings.

    Raises
    ------
    ValueError : unknown schema specified, or tablenames omitted and schema
                 not specified

    Examples
    --------
    >>> make_table_names('site', 'origin', owner='global', prefix='TA_')
    ('global.TA_site', 'global.TA_origin')

    >>> make_table_names(schema='css3', prefix='TA_')
    ('TA_affiliation', 'TA_assoc')
    ...


    """
    # XXX: is this function really necessary?
    prefix = kwargs.pop('prefix', '')
    owner = kwargs.pop('owner', None)
    schema = kwargs.pop('schema', None)

    if kwargs:
        msg = "Unknown keyword(s): {}".format(kwargs.keys())
        raise ValueError(msg)

    if not tables:
        if schema == 'css3':
            CORETABLES = css3.CORETABLES
        elif schema == 'kbcore':
            CORETABLES = kb.CORETABLES
        else:
            msg = "Unknown schema: {}".format(schema)
            raise ValueError(msg)

        tables = CORETABLES.keys()

    if owner:
        fmt = "{owner}.{prefix}{table}"
    else:
        fmt = "{prefix}{table}"

    tablenames = {}
    for table in tables:
        tablenames[table] = fmt.format(owner=owner, prefix=prefix, table=table)

    return tablenames


def make_tables(*tables, **kwargs):
    """
    Create mapped SQLAlchemy table classes.

    Parameters
    ----------
    tables : str
        Desired table names.  If omitted, a schema must be specified, and all
        core tables for the schema are returned.
    schema : str  ("css3" or "kbcore")
        Which set of core tables are being used. If omitted, tables must be
        specified.
    prefix : str
        All table names will have the provided prefix.
        e.g. "TA_" for "TA_origin", "TA_wfdisc", etc.
    owner : str
        e.g. "myuser" for "myuser.origin", "myuser.wfdisc", etc.

    Returns
    -------
    list
        Corresponding list of mapped SQLAlchemy table classes.

    """
    prefix = kwargs.pop('prefix', '')
    owner = kwargs.pop('owner', None)
    schema = kwargs.pop('schema', None)

    if kwargs:
        msg = "Unknown keyword(s): {}".format(kwargs.keys())
        raise ValueError(msg)

    tablenames = make_table_names(*tables, schema=schema, prefix=prefix,
                                    owner=owner)


def load_tables(session, *tables, schema=None, prefix="", owner=None):
    """
    Load mapped SQLAlchemy table classes from existing SQL tables.

    session : sqlalchemy.orm.Session
        Session connected to the target database.
    tables : str
        Desired table names.  If omitted, a schema must be specified, and all
        core tables for the schema are returned.
    schema : str  ("css3" or "kbcore")
        Which set of core tables are being used. If omitted, tables must be
        specified.
    prefix : str
        All table names will have the provided prefix.
        e.g. "TA_" for "TA_origin", "TA_wfdisc", etc.
    owner : str
        e.g. "myuser" for "myuser.origin", "myuser.wfdisc", etc.

    Returns
    -------
    list
        Corresponding list of mapped SQLAlchemy table classes.

    """
    pass


def init_tables(session, *tables):
    pass


def drop_tables(session, *tables):
    pass
