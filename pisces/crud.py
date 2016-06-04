"""
Module containing functions for in-memory and in-database table creation and
in-database table dropping.

Supports:
* table schema/accounts/owners/namespaces. SQLAlchemy calls them "schema."
* prefixed table names for standard table prototypes
* loading arbitrary tables from existing database
* creating standard prototype tables

Supported actions are:
* creating in-memory canonical tables



Glossary
--------
* table : canonical table name string, like "site"
* tablename : the fully-qualified table name string (includes any owner, prefix)
* mapped table : a SQLAlchemy ORM table class
* table instance / row : an instance of a mapped table

"""
# TODO: support plugging in additional schema

import pisces.tables.css3 as css3
import pisces.tables.kbcore as kb

def make_table_names(*tables, **kwargs):
    """
    Get table name strings in the format: <owner.><prefix>tablename

    Parameters
    ----------
    tables : str
        Desired table names.  If omitted, a schema must be specified, and all
        core tables for the schema are used.
    schema : str  {'css3', 'kbcore'}
        Which set of core tables are being used. If omitted, one or more tables
        must be specified.
    prefix : str
        All table names will have the provided prefix.
        e.g. "TA_" for "TA_origin", "TA_wfdisc", etc.
    owner : str
        e.g. "myuser" for "myuser.origin", "myuser.wfdisc", etc.

    Returns
    -------
    tablenames : dict
        The desired formatted table name strings, keyed by canonical name.

    Raises
    ------
    ValueError : unknown schema specified, or tablenames omitted and schema
                 not specified

    Examples
    --------
    >>> make_table_names('site', 'origin', owner='global', prefix='TA_')
    {'site': 'global.TA_site', 'origin': 'global.TA_origin'}

    >>> make_table_names(schema='css3', prefix='TA_')
    {'affiliation': 'TA_affiliation', 'assoc': 'TA_assoc', ...}


    """
    # TODO: is this function really necessary?  remove it.
    # >>> tables = [owner + '.' + prefix + table.name for table in coretables]
    # >>> tables = [prefix + table.name for table in coretables]
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
        Which set of core tables are being used. If omitted, "tables" must be
        specified.
    prefix : str
        All table names will have the provided prefix.
        e.g. "TA_" for "TA_origin", "TA_wfdisc", etc.
    owner : str
        e.g. "myuser" for "myuser.origin", "myuser.wfdisc", etc.

    Returns
    -------
    dict
        Corresponding dict of mapped SQLAlchemy table classes, keyed by
        canonical name.

    """
    prefix = kwargs.pop('prefix', '')
    owner = kwargs.pop('owner', None)
    schema = kwargs.pop('schema', None)

    if kwargs:
        msg = "Unknown keyword(s): {}".format(kwargs.keys())
        raise ValueError(msg)

    tablenames = make_table_names(*tables, schema=schema, prefix=prefix,
                                  owner=owner)
    # have dict of full table names 



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
