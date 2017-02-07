import os
import sys
import glob
import argparse
import imp

from sqlalchemy import create_engine
import sqlalchemy.exc as exc
import sqlalchemy.orm.exc as oexc

from obspy import read
from obspy.io.sac.core import _is_sac

import pisces as ps
from pisces.util import get_lastids, url_connect
from pisces.tables.kbcore import CORETABLES
import pisces.io.sac as sac


def get_plugins(plugins):
    """
    Returns a list of imported plugin function objects from a list of plugin
    strings, like path/to/module_file:plugin_function .

    """
    plugin_functions = []
    if plugins:
        for plugin_string in plugins:
            try:
                pth, fn = plugin_string.split(':')
            except ValueError:
                msg = "Must specify plugin like: path/to/modulename:plugin_function"
                raise ValueError(msg)
            pth = pth.split(os.path.sep)
            modname = pth.pop(-1)
            f, pathname, descr = imp.find_module(modname, pth)
            mod = imp.load_module(modname, f, pathname, descr)
            plugin_functions.append(getattr(mod, fn))

    return plugin_functions


def get_files(file_list):
    """
    Return a sequence of SAC file names from either a list of file names
    (trivial) or a text file list (presumable because there are too many files
    to use normal shell expansion).

    """
    if len(file_list) == 1 and not _is_sac(file_list[0]):
        #make a generator of non-blank lines
        try:
            listfile = open(file_list[0], 'r')
            files = (line.strip() for line in listfile if line.strip())
        except IOError:
            msg = "{0} does not exist.".format(file_list[0])
            raise IOError(msg)
    else:
        files = file_list

    return files


# TODO: put in util.py ?
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
    for table, dcts in dicts.items():
        cls = classes[table]
        dicts[table] = [cls(**dct) for dct in dcts]

    return dicts


def make_atomic(last, **rows):
    """
    Unify related table instances/row, including: ids, dir, and dfile
    """
    # last is an AttributeDict of {'keyvalue': lastid instance, ...}
    # rows is a dictionary of {'canonical tablename': [list of instances], ...}
    # of _related_ instances from a single SAC header?
    # TODO: check existance of rows before changing their ids.

    #print rows
    # the order matters here

    # for SAC, only 1
    for event in rows.get('event', []):
        # skips if no 'event' key and if 'event' value is empty []
        # XXX: check for existence first
        event.evid = next(last.evid)

    # for SAC, only 1
    for origin in rows.get('origin', []):
        # XXX: check for existance first
        origin.orid = next(last.orid)
        origin.evid = event.evid

    # for SAC, only 1
    for affil in rows.get('affiliation', []):
        pass

    # for SAC, only 1
    for sitechan in rows.get('sitechan', []):
        # XXX: check for existance first
        sitechan.chanid = next(last.chanid)

    # arrivals correspond to assocs
    for (arrival, assoc) in zip(rows.get('arrival', []), rows.get('assoc', [])):
        arrival.arid = next(last.arid)
        arrival.chanid = sitechan.chanid

        assoc.arid = arrival.arid
        assoc.orid = origin.orid

    # for SAC, only 1
    for wfdisc in rows.get('wfdisc', []):
        wfdisc.wfid = next(last.wfid)


def apply_plugins(plugins, **rows):
    for plugin in plugins:
        rows = plugin(**rows)

    return rows


def sac2db(session, tables, files, plugins=None, absolute_paths=False):
    pass

# TODO: make this main also accept a get_iterable and get_row_dicts functions,
#   so it can be renamed to iter2db and re-used in a sac2db.py and miniseed2db.py
def main(**kwargs):
    """
    Command-line arguments are created and parsed, fed to functions.

    Parameters
    ----------
    session : SQLAlchemy.orm.Session instance
    tables : list
        Canonical names for desired database tables.
    prefix : str
        Target core tables using 'account.prefix' naming.
    absolute_paths : bool
    bbfk : bool
        Pull in deast & dnorth info from user7 & user8 header fields
    file_list : str
        Name of a text file containing full SAC file names.
    files : list
        List of SAC file names.

    """
    print("sac2db: {}".format(kwargs))
    session = kwargs['session']

    if kwargs.get('file_list'):
        files = get_files(kwargs['file_list'])
    else:
        files = kwargs['files']

    tables = get_or_create_tables(session, create=True)

    lastids = ['arid', 'chanid', 'evid', 'orid', 'wfid']
    last = get_lastids(session, tables['lastid'], lastids, create=True)

    # for item in iterable:
    for sacfile in files:
        print(sacfile)

        # row_dicts = get_row_dicts(item)

        tr = read(sacfile, format='SAC', debug_headers=True)[0]

        # rows needs to be a dict of lists, for make_atomic
        # row_dicts = get_row_dicts(tr.stats.sac) # put in the whole trace, to determine byte order?
        dicts = sac.sachdr2tables(tr.stats.sac, tables=tables.keys())
        # row_instances = dicts_to_instances(row_dicts, tables)
        rows = dicts2rows(dicts, tables)

        # manage dir, dfile, datatype
        # XXX: hack.  replace with an updated obspy.io.sac later.
        bo = tr.data.dtype.byteorder
        if bo == '<':
            datatype = 'f4'
        elif bo == '>':
            datatype = 't4'
        elif bo == '=':
            if sys.byteorder == 'little':
                datatype = 'f4'
            else:
                datatype = 't4'

        for wf in rows['wfdisc']:
            wf.datatype = datatype
            wf.dfile = os.path.basename(sacfile)
            if kwargs['absolute_paths']:
                idir = os.path.dirname(os.path.realpath(sacfile))
            else:
                idir = os.path.dirname(sacfile)
                # make sure relative paths are non-empty
                if idir == '':
                   idir = '.'
            wf.dir = idir

        # manage the ids
        make_atomic(last, **rows)

        # plugins = get_plugins(options)

        # rows = apply_plugins(plugins, **rows)

        # add rows to the database
        # XXX: not done very elegantly.  some problem rows are simply skipped.
        for table, instances in rows.items():
            if instances:
                # could be empty []
                try:
                    session.add_all(instances)
                    session.commit()
                except exc.IntegrityError as e:
                    # duplicate or nonexistant primary keys
                    session.rollback()
                    print("rollback {}".format(table))
                except exc.OperationalError as e:
                    # no such table, or database is locked
                    session.rollback()
                    print("rollback {}".format(table))
