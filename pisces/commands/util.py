"""
Helper functions for comman-line utilities.

"""
from pisces.tables.kbcore import CORETABLES


def get_or_create_tables(session, prefix=None, create=True, **tables):
    """
    Load or create canonical ORM KB Core table classes.

    Parameters
    ----------
    session : sqlalchemy.orm.Session
    prefix : str
        Prefix for canonical table names, e.g. 'myaccount.' or 'TA_' (no owner/schema).
        Canonical table names are used if no prefix is provided.
    create : bool
        If True, create tables that don't yet exist.

    Canonical table keyword/tablename string pairs, such as site='other.site',
    can override prefix.  For example, you may want to use a different Lastid
    table, so that ids don't start from 1.

    Returns
    -------
    tables : dict
        A mapping between canonical table names and SQLA declarative classes
        with the correct __tablename__.
        e.g. {'origin': Origin, ...}

    """
    # The Plan:
    # 1. For each core table, build or get the table name
    # 2. If it's a vanilla table name, just use a pre-packaged table class
    # 3. If not, try to autoload it.
    # 4. If it doesn't exist, make it from a prototype and create it in the database.

    # TODO: check options for which tables to produce.

    if not prefix:
        prefix = ''

    tabledict = {}
    for coretable in CORETABLES.values():
        # build the table name
        fulltablename = tables.get(coretable.name, prefix + coretable.name)

        # put table classes into the tables dictionary
        if fulltablename == coretable.name:
            # it's a vanilla table name. just use a pre-packaged table class instead of making one.
            tabledict[coretable.name] = coretable.table
        else:
            tabledict[coretable.name] = ps.make_table(fulltablename, coretable.prototype)

        tabledict[coretable.name].__table__.create(session.bind, checkfirst=True)

    session.commit()

    return tabledict


def dicts2rows(dicts, classes):
    """
    Expands lists of table dictionaries into table class instances.

    dicts : dict
        Keys are canonical table names, values are lists of row dicts for that table.
    classes : dict
        Keys are canonical table names, values are table classes.

    """
    for table, dcts in dicts.items():
        cls = classes[table]
        dicts[table] = [cls(**dct) for dct in dcts]

    return dicts

def get_files(file_list, file_check=None):
    """
    Return a sequence of file names from either a list of file names
    (trivial) or a text file list (presumable because there are too many files
    to use normal shell expansion).

    Optionally, supply a file_check function that accepts a file name, and returns
    a boolean True if the file is the desired format.  This only checks the first
    file, and raises an IOError if False, assuming all subsequent files will be
    the wrong format.

    """
    if len(file_list) == 1 and not file_check(file_list[0]):
        #make a generator of non-blank lines
        try:
            with open(file_list[0], 'r') as listfile:
                files = (line.strip() for line in listfile if line.strip())
        except IOError:
            msg = "{0} does not exist.".format(file_list[0])
            raise IOError(msg)
    else:
        files = file_list

    return files
