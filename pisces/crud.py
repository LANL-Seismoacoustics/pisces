# -*- coding: utf-8 -*-
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
* table : canonical table name string, like "site" or "origin"
* tablename : the fully-qualified table name string (includes any owner, prefix)
* mapped table : a SQLAlchemy ORM table class
* table instance / row : an instance of a mapped table

"""
# TODO: support plugging in additional schema
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base

from pisces.schema.util import PiscesMeta
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
    dict
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
    # TODO: is this function really necessary?  remove it?
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


def split_table_names(*tablenames, **kwargs):
    """
    Splits full table names into a (owner, prefix, tablename) 3-tuples.

    Parameters
    ----------
    tablenames : str
    schema : str {'css3', 'kbcore'} Default 'css3'.
    split_prefix : bool, default True
        If True, return (owner, prefix, tablename) tuples,
        otherwise return (owner, tablename) tuples.

    Returns
    -------
    list
        Corresponding list of (owner, tablename) or (owner, prefix, tablename)
        tuples strings. Empty owner or prefix are ''.

    Examples
    --------
    >>> tablenames = ['global.site', 'global.sitechan', 'TA_site',
    ...               'different_acct.my_origin', 'myfriend.discrim_last']
    >>> split_table_names(*tablenames)
    [('global', '', 'site'), ('global', '', 'sitechan'), ('', 'TA_', 'site'),
    ('different_acct', 'my_', 'origin'), ('myfriend', '', 'discrim_last')]

    """
    split_prefix = kwargs.pop('split_prefix', True)
    schema = kwargs.get('schema', 'css3')
    if schema == 'css3':
        schematables = css3.CORETABLES.keys()
    elif schema == 'kbcore':
        schematables = kb.CORETABLES.keys()
    else:
        msg = "Unknown schema: {}".format(schema)
        raise ValueError(msg)

    out = []
    for fulltablename in tablenames:
        try:
            owner, prefixed_tablename = fulltablename.split('.')
        except ValueError:
            owner = ''
            prefixed_tablename = fulltablename

        if split_prefix:
            # if a table 'endswith' a table in the schema, the part before is the
            # table prefix
            for schematable in schematables:
                head, sep, tail = prefixed_tablename.rpartition(schematable)
                if sep and not tail:
                    prefix = head
                    tablename = schematable
                elif not sep:
                    prefix = ''
                    tablename = tail

            out.append((owner, prefix, tablename))
        else:
            out.append((owner, prefixed_tablename))


    return out


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
        Desired table names.  Table name must be known to the schema. 
        If omitted, a schema must be specified, and all core tables for the
        schema are returned.
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
    >>> # makes a dict of CSS3.0 'TA_site' and 'TA_sitechan' mapped classes
    >>> tables = make_tables('site', 'sitechan', schema='css3', prefix='TA_')

    >>> # make a dict of all standard kbcore tables
    >>> tables = make_tables(schema='kbcore')

    >>> # make a dict of some tables from the 'myowner' account
    >>> tables = make_tables('origin', 'event', schema='kbcore', owner='myowner')

    """
    # if there is an owner or a prefix, the tables need to be created
    # otherwise, just return the existing ones.

    # TODO: find a way to not repeat arguments with all these functions
    prefix = kwargs.get('prefix', '')
    owner = kwargs.get('owner', None)
    schema = kwargs.get('schema', 'css3')

    if schema == 'css3':
        CORETABLES = css3.CORETABLES
    elif schema == 'kbcore':
        CORETABLES = kb.CORETABLES
    else:
        msg = "Unknown schema: {}".format(schema)
        raise ValueError(msg)

    non_schema_tables = set(tables) - set(CORETABLES.keys())
    if non_schema_tables:
        msg = "Unknown tables: {}".format(non_schema_tables)
        raise ValueError(msg)

    # I don't use 'owner' here, b/c we will be making classes. 'owner' is used
    # in making the declarative base class and a non-owner-qualified tablename
    # is used in the __tablename__
    tablenames = make_table_names(*tables, schema=schema, prefix=prefix)

    if owner:
        parents = (declarative_base(metadata=sa.metaData(schema=owner)),)
    else:
        parents = ()

    # "out" will hold concrete classes
    # go through one by one & repace names w/ classes
    # if a standard table, get the prototype concrete class
    out = {}
    for table, tablename in tablenames.items():
        prototype = CORETABLES[table].prototype
        # TODO: capitalize tablename?
        out[table] = type(tablename, parents + (prototype,),
                          {'__tablename__': tablename})

    return out


def load_tables(session, *tables, **kwargs):
    """
    Load existing database tables into mapped SQLAlchemy table classes.

    This function is not recommended.  Instead, please subclass from an
    existing abstract table in the schema, or use the SQLAlchemy ORM to create
    a class for your table.

    session : sqlalchemy.orm.Session
        Session connected to the target database.
    tables : str
        Desired table names.  Names must be part of the schema. If omitted, a
        schema must be specified, and all core tables for the schema are
        returned.
    schema : str  {'css3', 'kbcore'}  Default, 'css3'
        Which set of core tables are being used.  This is used to associate
        column names to known Pisces column definitions, so that text file I/O
        of tables can be supported for a loaded table.
    prefix : str, optional
        All table names will have the provided prefix.
        e.g. "TA_" for "TA_origin", "TA_wfdisc", etc.
    owner : str, optional
        e.g. "myuser" for "myuser.origin", "myuser.wfdisc", etc.  If omitted, 
        the database default owner/account will be used.
    primary_keys : dict, optional
        A mapping of table names to their primary keys of the form,
        {'tablename1': ['primary_key1', 'primary_key2'], ...}
        The SQLAlchemy ORM can only reflect/load tables if they have a primary
        key. If a table is a view or has no primary key, these must be
        specified explicitly.

    Returns
    -------
    dict
        Corresponding dict of mapped SQLAlchemy table classes, keyed by
        canonical name.

    Examples
    --------
    # load standard tables in 'myaccount' table space
    >>> tables = load_tables(session, 'site', 'sitechan', 'wfisc',
    ...                      schema='kbcore', owner='myaccount')

    # load a standard table that has no primary key set
    >>> tables = load_tables(session, 'site', 
    ...                      primary_keys={'site', ['sta', 'ondate']})

    # load all standard css3 tables in the default account
    >>> tables = load_tables(session, schema='css3')


    # load a table that is outside of the schema
    # the table needs to have a primary key defined
    # this will try to use column info definitions known to Pisces
    >>> tables = load_tables(session, 'ccwfdisc', owner='myaccount')

    """
    # TODO: Use sqlalchemy.ext.automap.automap_base inside this function?
    # TODO: After conversion to Python 3, use something better than **kwargs.
    schema = kwargs.get('schema', 'css3')
    prefix = kwargs.get('prefix', '')
    owner = kwargs.get('owner', None)

    # I don't use 'owner' here, b/c it will be enforced by the MetaData. Here,
    # we nust need table names.
    tablenames = make_table_names(*tables, schema=schema, prefix=prefix)

    if owner:
        parents = (declarative_base(metadata=sa.MetaData(schema=owner),
                                    constructor=None, metaclass=PiscesMeta),)
    else:
        parents = ()

    colinfo = getattr(parents, '_column_info_registry', {})

    metadata = sa.MetaData()

    table_classes = dict()
    for table, tablename in tablenames.items():
        itable = sa.Table(tablename, metadata, autoload=True,
                          autoload_with=session.bind, schema=owner)
        if colinfo:
            for col in itable.columns:
                col.info.update(colinfo.get(col.name, {}))

        classdict = {'__table__': itable}

        if primary_keys and tablename in primary_keys:
            columns = [getattr(itable.columns, key) for key in primary_keys[tablename]]
            classdict['__mapper_args__'] = {'primary_key': columns}

        ORMTable = type(tablename.capitalize(), parents, classdict)

        table_classes[table] = ORMTable

    return table_classes


def init_tables(session, *tables):
    """
    Create table classes in a database.

    Parameters
    ----------
    session : sqlalchemy.orm.Session instance
    tables : mapped table classes

    """
    for itable in tables:
        itable.__table__.create(session.bind)
    session.commit()


def drop_tables(session, *tables):
    """
    Drop table classes in a database.

    Parameters
    ----------
    session : sqlalchemy.orm.Session instance
    tables : mapped table classes

    """
    for itable in tables:
        itable.__table__.drop(session.bind)
    session.commit()

