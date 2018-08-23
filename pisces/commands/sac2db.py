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
import pisces.io.sac as sac
from .util import get_or_create_tables, dicts2rows, get_files


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


def make_atomic(last, **rows):
    """
    Unify related table instances/row, including: ids, dir, and dfile

    Parameters
    ----------
    last : obspy.AttributeDict
        {'keyvalue': lastid instance, ...}
    rows : dict
        {'canonical tablename': [list of row instances], ...} of _related_
        instances from a single SAC header?
    """
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
        files = get_files(kwargs['file_list'], file_check=_is_sac)
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

        # sachdr2tables produces table dictionaries
        # rows needs to be a dict of lists, for make_atomic
        dicts = sac.sachdr2tables(tr.stats.sac, tables=tables.keys())
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
