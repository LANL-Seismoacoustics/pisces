import glob
from collections import namedtuple
from optparse import OptionParser

import sqlalchemy.exc as exc
import sqlalchemy.orm.exc as oexc

import pisces as ps
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
def split_slash(option, opt_str, value, parser):
    setattr(parser.values, option.dest, [float(val) for val in value.split("/")])

def split_comma(option, opt_str, value, parser):
    setattr(parser.values, option.dest, [val.strip() for val in value.split(",")])

def expand_glob(option, opt_str, value, parser):
    """Returns an iglob iterator for file iteration. Good for large file lists."""
    setattr(parser.values, option.dest, glob.iglob(value))


def get_parser():
    """
    This is where the command-line options are defined, to be parsed from argv

    Returns
    -------
    optparse.OptionParser instance

    Examples
    -------
    Test the parser with this syntax:

    >>> from sac2db import get_parser
    >>> parser = get_parser()
    >>> options, args = parser.parse_args(['-f','*.sac','dbout'])
    >>> print options
    {'origin': None, 'site': None, 'wfdisc': None, 'affiliation': None, 'port':
    '', 'conn': None, 'backend': 'sqlite', 'all_tables': None, 'instance': '',
    'event': None, 'instrument': None, 'arrival': None, 'sitechan': None,
    'psswd': '', 'assoc': None, 'user': '', 'f': <generator object iglob at
    0x10c782f50>, 'l': None, 'server': '', 't': None, 'lastid': None,
    'rel_path': False, 'gndd': False}
    >>> print args
    ['dbout']

    """
    parser = OptionParser(usage="Usage: %prog [options] ",
            description="""Write data from SAC files into a database.""",
            version='0.2')
    parser.add_option('-f','--files',
            default=None,
            help="Unix-style file name expansion for trace files.",
            type='string',
            action="callback",
            callback=expand_glob,
            dest='f')
    parser.add_option('-l','--list',
            default=None,
            help="A text file containing a column of trace file names.",
            type='string',
            dest='l')
    parser.add_option('-t','--tables',
            help="Only parse into this comma-seperated list of tables.",
            default=None,
            action='callback',
            callback=split_comma,
            dest='t')
    parser.add_option('--conn',
            default=None,
            help="SQLAlchemy-style output database connection string.",
            type='string',
            dest='conn')
    parser.add_option('-u', '--user',
            default='',
            help="Database user name. Not needed for sqlite and remotely \
                  authenticated connections.",
            type='string',
            dest='user')
    parser.add_option('-b', '--backend',
            default='sqlite',
            help="SQLAlchemy-style backend and driver string.",
            type='string',
            dest='backend')
    parser.add_option('-p', '--psswd',
            default='',
            help="Database password.  Not needed for sqlite and remotely \
                  authenticated connections.  Prompted for if needed and \
                  not given.",
            type='string',
            dest='psswd')
    parser.add_option('-s', '--server',
            default='',
            help="Local or remote database server. Not needed for sqlite.",
            type='string',
            dest='server')
    parser.add_option('--port',
            default='',
            help="Port on database server.  Optional.",
            type='string',
            dest='port')
    parser.add_option('-i', '--instance',
            default='',
            help="Database instance name.  Optional for some backends.\
                  For sqlite, this is the file name.",
            type='string',
            dest='instance')
    parser.add_option('--gndd',
            default=False,
            help="Convenience flag for GNEM database users. \
                  Sets server, port, instance, and backend.",
            action='store_true',
            dest='gndd')
    parser.add_option('--rel_path',
            default=False,
            help="Write directories ('dir') as relative paths, not absolute.",
            action='store_true',
            dest='rel_path')
    # ----------------------- Add core table arguments ------------------------
    #The following loop adds core table options.  They look like:
    #parser.add_option('--origin',
    #        default=None,
    #        help="Name of desired output origin table.  Optional.  \
    #              No owner for sqlite.",
    #        type='string',
    #        metavar='owner.tablename',
    #        dest='origin')
    for coretable in CORETABLES:
        parser.add_option('--' + coretable.name,
                          default=None,
                          help="Name of desired output {} table.  Optional. \
                                No owner for sqlite.".format(coretable.name),
                          type='string',
                          metavar='owner.tablename',
                          dest=coretable.name)
    # -------------------------------------------------------------------------
    parser.add_option('--all_tables',
            default=None,
            help="Convenience flag.  Attempt to fill all tables.\
                  e.g. myaccount.test_ will attempt to produce tables \
                  like myaccount.test_origin, myaccount.test_sitechan.\
                  Not yet implemented.",
            type='string',
            metavar='owner.prefix',
            dest='all_tables')

    return parser


def get_session(options):
    if options.gndd:
        #TODO: add a password option here
        try:
            from pisces_gndd import gndd_connect
            session = gndd_connect(options.user)
        except ImportError as e:
            msg = "Must have pisces_gndd installed with --gndd option."
            raise ImportError(msg)
    else:
        if options.conn:
            session = ps.db_connect(conn=options.conn)
        else:
            session = ps.db_connect(user=options.user,
                                    psswd=options.psswd,
                                    backend=options.backend,
                                    server=options.server,
                                    port=options.port,
                                    instance=options.instance)

    return session


def get_or_create_tables(options, session, create=True):
    """
    Load or create canonical ORM KB Core table classes.

    Parameters
    ----------
    options : optparse.OptionParser
    session : sqlalchemy.orm.Session

    Returns
    -------
    tables : dict
        Canonical table names and mapped classes, like: {'tablename': class, ...}

    """
    # The Plan:
    # 1. For each core table, build or get the table name
    # 2. If it's a vanilla table name, just use a pre-packaged table class
    # 3. If not, try to autoload it.
    # 4. If it doesn't exist, make it from a prototype and create it in the database.
    tables = {}
    for coretable in CORETABLES:
        # build the table name
        if options.all_tables is None:
            fulltabnm = getattr(options, coretable.name, None)
        else:
            fulltabnm = options.all_tables + coretable.name

        if fulltabnm == coretable.name:
            # it's a vanilla table name. just use a pre-packaged table class
            tables[coretable.name] = coretable.table
        else:
            try:
                # autoload a custom table name and/or owner
                tables[coretable.name] = ps.get_tables(session.bind, [fulltabnm])[0]
            except exc.NoSuchTableError as e:
                if create:
                    # user wants to make one and create it
                    print "{0} doesn't exist. Creating it.".format(fulltabnm)
                    tables[coretable.name] = ps.make_table(fulltabnm, coretable.prototype)
                    tables[coretable.name].__table__.create(session.bind, checkfirst=True)
                else:
                    # user expected the table to be there
                    raise e

    return tables


def get_files(options):
    """
    returns a sequence of files (names?)
    raises IOError if problematic
    raises ValueError if problematic
    """
    if options.f is not None:
        files = options.f
    elif options.l is not None:
        try:
            lfile = open(options.l, 'r')
            #make a generator of non-blank lines
            files = (line.strip() for line in lfile if line.strip())
        except IOError:
            msg = "{0} does not exist.".format(options.l)
            raise IOError(msg)
    else:
        msg = "Must provide input files or file list."
        raise ValueError(msg)

    return files


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


def manage_rows(session, last, **rows):
    """
    Unify related table instances/row, including: ids, dir, and dfile
    """
    # last is an AttributeDict of {'keyvalue': lastid instance, ...}
    # rows is a dictionary of {'canonical tablename': [list of instances], ...}
    # of _related_ instances from a single SAC header?
    # TODO: check existance of rows before changing their ids.

    # the order matters here

    # for SAC, only 1
    for event in rows.get('event', []):
        # skips if no 'event' key and if 'event' value is empty []
        # XXX: check for existance first
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

    options, args = parser.parse_args(argv)

    session = get_session(options)

    tables = get_or_create_tables(options, session, create=True)

    files = get_files(options)

    lastids = ['arid', 'chanid', 'evid', 'orid', 'wfid']
    last = ps.get_lastids(session, tables['lastid'], lastids, create=True)

    for sacfile in files:
        print sacfile

        tr = read(sacfile, format='SAC', debug_headers=True)

        rows = sac.sachdr2tables(tr.stats.sac, tables=tables.keys())
        rows = sac2db(sacheader, last, **tables)

        # manage the ids
        manage_rows(session, last, **rows)

        # manage dir, dfile


        for table, instances in rows.items():
            if instances:
                # could be empty []
                try:
                    session.add_all(instances)
                    session.commit()
                except IntegrityError as e:
                    # duplicate or nonexistant primary keys
                    session.rollback()
                except OperationalError as e:
                    # no such table, or database is locked
                    session.rollback()


if __name__ == '__main__':
    main(sys.argv)
