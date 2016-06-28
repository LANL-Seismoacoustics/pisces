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
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

import pisces.tables.css3 as css3
import pisces.tables.kbcore as kb

def make_table_names(*tables, **kwargs):
    """
    Get table name strings in the format: {owner.}{prefix}tablename

    This function does no checking that supplied table names are in the
    indicated schema.

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
    prefix = kwargs.get('prefix', '')
    owner = kwargs.get('owner', None)
    schema = kwargs.get('schema', None)

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
    Create mapped SQLAlchemy ORM table classes.

    If no owner or prefix is indicated, the returned tables are the same as
    those in pisces.tables.<schema> .  The user is encouraged to import these
    classes directly. If an owner is indicated, returned tables inhererit from
    the same SQLA declarative base.

    Parameters
    ----------
    tables : str
        Desired table names.  If omitted, a schema must be specified, and all
        core tables for the schema are returned.
    schema : str  ("css3" or "kbcore")
        Which set of core tables are being used.  Required.
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

    Examples
    --------
    >>> # makes CSS3.0 'TA_site' and 'TA_sitechan' mapped classes
    >>> tables = make_tables('site', 'sitechan', schema='css3', prefix='TA_')

    >>> # get all standard kbcore tables
    >>> tables = make_tables(schema='kbcore')

    >>> # get some tables from the 'myowner' account
    >>> tables = make_tables('origin', 'event', schema='kbcore', owner='myowner')

    """
    # TODO: find a way to not repeat arguments with all these functions
    prefix = kwargs.get('prefix', '')
    owner = kwargs.get('owner', None)
    schema = kwargs.get('schema', None)

    # resolve table names and schema
    if not tables and not schema:
        msg = "If tables are not specified, schema must be specified."
        raise ValueError(msg)

    if not owner and not prefix:
        STANDARD_TABLES = True
    else:
        STANDARD_TABLES = False

    tablenames = make_table_names(*tables, schema=schema, prefix=prefix,
                                  owner=owner)

    if schema == 'css3':
        CORETABLES = css3.CORETABLES
    elif schema == 'kbcore':
        CORETABLES = kb.CORETABLES
    else:
        msg = "Unknown schema: {}".format(schema)
        raise ValueError(msg)

    if owner:
        parents = (declarative_base(metadata=sa.metaData(schema=owner)), )
    else:
        parents = ()

    # if not standard tables, get the prototype table
    tables = tablenames.copy()
    for tabletype, tablename in tables.items():


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
