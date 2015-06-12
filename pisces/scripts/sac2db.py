#!/usr/bin/env python
import os
import sys
import glob
from collections import namedtuple
from optparse import OptionParser
import argparse

from sqlalchemy import create_engine
import sqlalchemy.exc as exc
import sqlalchemy.orm.exc as oexc

from obspy import read
from obspy.sac.core import isSAC

import pisces as ps
from pisces.util import get_lastids, url_connect
import pisces.schema.kbcore as kba
import pisces.tables.kbcore as kb
import pisces.io.sac as sac

# user supplies their own class, inherited from kbcore, or just uses .tables
# the prototype tables have a .from_sac or .from_mseed classmethod.

# for readability, use these named tuples for core tables, like:
# tab = CORETABLES[7]
# tab.name is 'site', tab.prototype is the abstract Site class,
# and tab.table is an actual Site table
CoreTable = namedtuple('CoreTable', ['name', 'prototype', 'table'])
CORETABLES = [CoreTable('affiliation', kba.Affiliation, kb.Affiliation),
              CoreTable('arrival', kba.Arrival, kb.Arrival),
              CoreTable('assoc', kba.Assoc, kb.Assoc),
              CoreTable('event', kba.Event, kb.Event),
              CoreTable('instrument', kba.Instrument, kb.Instrument),
              CoreTable('lastid', kba.Lastid, kb.Lastid),
              CoreTable('origin', kba.Origin, kb.Origin),
              CoreTable('site', kba.Site, kb.Site),
              CoreTable('sitechan', kba.Sitechan, kb.Sitechan),
              CoreTable('wfdisc', kba.Wfdisc, kb.Wfdisc)]

# HELPER FUNCTIONS
def expand_glob(option, opt_str, value, parser):
    """Returns an iglob iterator for file iteration. Good for large file lists."""
    setattr(parser.values, option.dest, glob.iglob(value))

def get_parser():
    """
    This is where the command-line options are defined, to be parsed from argv

    Returns
    -------
    argparse.ArgumentParser instance

    Examples
    -------
    Test the parser with this syntax:

    >>> from sac2db import get_parser
    >>> parser = get_parser()
    >>> options = parser.parse_args(['--origin', 'origin', '--affiliation',
                                     'myaffiliation', '*.sac', 
                                     'sqlite://mydb.sqlite'])
    >>> print options
    Namespace(affiliation='my.affiliation', all_tables=None, arrival=None,
    assoc=None, event=None, files=['*.sac'], instrument=None, lastid=None,
    origin='origin', rel_path=False, site=None, sitechan=None, 
    url='sqlite://mydb.sqlite', wfdisc=None)

    """
    parser = argparse.ArgumentParser(prog='sac2db',
            description="""
            Write data from SAC files into a database.
            
            If individual table name flags are specified, only those core
            tables are written from SAC file headers, otherwise all core tables
            are written to standard or prefixed table names.""",
            version='0.2')
    # ----------------------- Add core table arguments ------------------------
    #The following loop adds the core table owner/name options.
    for coretable in CORETABLES:
        parser.add_argument('--' + coretable.name,
                            default=None,
                            help="Name of desired output {} table.  Optional. \
                                  No owner for sqlite.".format(coretable.name),
                            metavar='owner.tablename',
                            dest=coretable.name)
    # -------------------------------------------------------------------------
    parser.add_argument('--absolute_paths',
            default=False,
            help="Write database 'dir' directory entries as absolute paths, not relative.",
            action='store_true',
            dest='rel_path')

    parser.add_argument('url',
            help="SQLAlchemy-style database connection string, such as \
            sqlite:///mylocaldb.sqlite or oracle://myuser@myserver.lanl.gov:8000/mydb")

    parser.add_argument('dbout',
            help="Target tables using 'account.prefix naming.'\
                  e.g. myaccount.test_ will target tables \
                  like myaccount.test_origin, myaccount.test_sitechan.\
                  Use '-' (no quotes) for default standard table names.")

    parser.add_argument('files',
            nargs='+',
            help="SAC file names, including any Unix-style name expansions.")

    return parser


def get_session(options):
    # accept command line arguments, return a database-bound session.
    session = url_connect(options.url)

    return session


def get_files(options):
    """
    Return a sequence of SAC file names from either a list of file names
    (trivial) or a text file list (presumable because there are too many files
    to use normal shell expansion).

    """
    if len(options.files) == 1 and not isSAC(options.files[0]):
        #make a generator of non-blank lines
        try:
            listfile = open(options.files[0], 'r')
            files = (line.strip() for line in listfile if line.strip())
        except IOError:
            msg = "{0} does not exist.".format(options.files[0])
            raise IOError(msg)
    else:
        files = options.files

    return files


def get_or_create_tables(options, session, create=True):
    """
    Load or create canonical ORM KB Core table classes.

    Parameters
    ----------
    options : argparse.ArgumentParser
    session : sqlalchemy.orm.Session

    Returns
    -------
    tables : dict
        Mapping between canonical table names and SQLA ORM classes.
        e.g. {'origin': MyOrigin, ...}

    """
    # The Plan:
    # 1. For each core table, build or get the table name
    # 2. If it's a vanilla table name, just use a pre-packaged table class
    # 3. If not, try to autoload it.
    # 4. If it doesn't exist, make it from a prototype and create it in the database.

    # New Plan:
    # 1. Always need a lastid. Check for it, maybe create it.

    dbout = options.dbout
    if dbout == '-':
        dbout = ''

    tables = {}
    for coretable in CORETABLES:
        # build the table name
        if getattr(options, coretable.name, None):
            fulltablename = getattr(options, coretable.name)
        else:
            fulltablename = dbout + coretable.name

        # fulltablename is either an arbitrary string or dbout + core name, but not None

        # put table classes into the tables dictionary
        if fulltablename == coretable.name:
            # it's a vanilla table name. just use a pre-packaged table class instead of making one.
            tables[coretable.name] = coretable.table
        else:
            tables[coretable.name] = ps.make_table(fulltablename, coretable.prototype)

        tables[coretable.name].__table__.create(session.bind, checkfirst=True)

    session.commit()

    return tables


def sac2db(sacfile, last, **tables):
    """
    Get core tables instances from a SAC file.

    Parameters
    ----------
    sacfile : str
        SAC file name
    last : dict
        The output from get_lastids: a dictionary of lastid keyname: instances.
    site, origin, event, wfdisc, sitechan : SQLA table classes with .from_sac

    """
    # XXX: this doesn't work (yet?)
    # TODO: remove id handling
    out = {}
    try:
        Lastid = tables.pop('lastid')
    except KeyError:
        msg = "Must include Lastid table."
        raise KeyError(msg)

    # required
    if 'site' in tables:
        Site = tables['site']
        out['site'] = Site.from_sac(item)
        # twiddle lastids here?

    if 'sitechan' in tables:
        # sitechan.ondate
        # sitechan.chanid
        if not sitechan.chanid:
            sitechan.chanid = last.chanid.next()

    if 'wfdisc' in tables:
        # XXX: Always gonna be a wfdisc, right?
        # XXX: Always writes a _new_ row b/c always new wfid
        # wfdisc.dir
        # wfdisc.dfile
        # wfdisc.wfid
        if options.rel_path:
            wfdisc.dir = os.path.dirname(ifile)
        else:
            wfdisc.dir = os.path.abspath(os.path.dirname(ifile))
        wfdisc.dfile = os.path.basename(ifile)
        wfdisc.wfid = last.wfid.next()

    if 'origin' in tables:
        Origin = tables['origin']
        out['origin'] = Origin.from_sac(item)
        # twiddle lastids here?

    if 'arrivals' in tables:
        Arrival = tables['arrival']
        out['arrival'] = Arrival.from_sac(item)

    if ('assoc' in tables) and ('arrivals' in tables):
        # assoc.arid
        # assoc.orid
        #XXX: assumes arrivals are related to origin
        # and assocs and arrivals are in the same order
        for (assoc, arrival) in zip(assocs, arrivals):
            assoc.arid = arrival.arid
            if hasattr(origin, 'orid'):
                assoc.orid = origin.orid

    return out

def dicts2rows(dicts, classes):
    # print dicts
    for table, dcts in dicts.items():
        #print table, dcts
        cls = classes[table]
        dicts[table] = [cls(**dct) for dct in dcts]

    return dicts

def make_atomic(session, last, **rows):
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



def main(argv=None):
    """
    Command-line arguments are created and parsed, fed to functions.

    """
    parser = get_parser()

    options = parser.parse_args(argv)
    #print options

    session = get_session(options)

    files = get_files(options)

    tables = get_or_create_tables(options, session, create=True)

    lastids = ['arid', 'chanid', 'evid', 'orid', 'wfid']
    last = get_lastids(session, tables['lastid'], lastids, create=True)

    for sacfile in files:
        print sacfile

        tr = read(sacfile, format='SAC', debug_headers=True)[0]

        # rows needs to be a dict of lists, for make_atomic
        dicts = sac.sachdr2tables(tr.stats.sac, tables=tables.keys())
        #rows = sac2db(tr.stats.sac, last, **tables)
        rows = dicts2rows(dicts, tables)

        # manage the ids
        make_atomic(session, last, **rows)

        # manage dir, dfile
        for wf in rows['wfdisc']:
            wf.dir = os.path.dirname(sacfile)
            wf.dfile = os.path.basename(sacfile)


        for table, instances in rows.items():
            if instances:
                # could be empty []
                try:
                    session.add_all(instances)
                    session.commit()
                except exc.IntegrityError as e:
                    # duplicate or nonexistant primary keys
                    session.rollback()
                    print("rollback")
                except exc.OperationalError as e:
                    # no such table, or database is locked
                    session.rollback()
                    print("rollback")


if __name__ == '__main__':
    main(sys.argv[1:])
