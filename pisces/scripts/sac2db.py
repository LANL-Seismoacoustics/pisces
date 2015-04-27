from optparse import OptionParser

import pisces as ps
import pisces.tables.kbcore as kb

# user supplies their own class, inherited from kbcore, or just uses .tables
# the prototype tables have a .from_sac or .from_mseed classmethod.

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
    This is where the command-line options are defined and parsed from argv
    """
    parser = OptionParser(usage="Usage: %prog [options] ",
            description="""Write data from sac or mseed headers into a database. Currently, only SAC files are supported.""",
            version='0.1')
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
    parser.add_option('--affiliation',
            default=None,
            help="Name of desired output affiliation table. Optional.  \
                  No owner for sqlite.",
            type='string',
            metavar='owner.tablename',
            dest='affiliation')
    parser.add_option('--arrival',
            default=None,
            help="Name of desired output arrival table.  Optional. \
                  No owner for sqlite.",
            type='string',
            metavar='owner.tablename',
            dest='arrival')
    parser.add_option('--assoc',
            default=None,
            help="Name of desired output assoc table.  Optional. \
                  No owner for sqlite.",
            type='string',
            metavar='owner.tablename',
            dest='assoc')
    parser.add_option('--event',
            default=None,
            help="Name of desired output event table.  Optional.  \
                  No owner for sqlite.",
            type='string',
            metavar='owner.tablename',
            dest='event')
    parser.add_option('--instrument',
            default=None,
            help="Name of desired output instrument table.  Optional.  \
                  No owner for sqlite.",
            type='string',
            metavar='owner.tablename',
            dest='instrument')
    parser.add_option('--origin',
            default=None,
            help="Name of desired output origin table.  Optional.  \
                  No owner for sqlite.",
            type='string',
            metavar='owner.tablename',
            dest='origin')
    parser.add_option('--site',
            default=None,
            help="Name of desired output site table.  Optional. \
                  No owner for sqlite.",
            type='string',
            metavar='owner.tablename',
            dest='site')
    parser.add_option('--sitechan',
            default=None,
            help="Name of desired output sitechan table.  Optional.",
            type='string',
            metavar='owner.tablename',
            dest='sitechan')
    parser.add_option('--wfdisc',
            default=None,
            help="Name of desired output wfdisc table.  Optional. \
                  No owner for sqlite. Currently always adds wfdisc rows.",
            type='string',
            metavar='owner.tablename',
            dest='wfdisc')
    parser.add_option('--lastid',
            default=None,
            help="Name of desired output lastid table.  Required.  \
                  No owner for sqlite.",
            type='string',
            metavar='owner.tablename',
            dest='lastid')
    parser.add_option('--all_tables',
            default=None,
            help="Convenience flag.  Attempt to fill all tables. \
                  e.g. jon.test_ will attempt to produce tables like \
                  jon.test_origin, jon.test_sitechan, ...\
                  Not yet implemented.",
            type='string',
            metavar='owner.prefix',
            dest='all_tables')
    parser.add_option('--gndd',
            default=False,
            help="""Convenience flag fills in server, port, instance, backend for gnem database users.""",
            action='store_true',
            dest='gndd')
    parser.add_option('--rel_path',
            default=False,
            help="Write directory entries as relative paths, not absolute.",
            action='store_true',
            dest='rel_path')    pass


def parse_tables(args):
    # returns dictionary of canonical {tablenames: classes} using ps.make_table
    pass


def parse_files(args):
    # returns an iterator of file names
    pass


def sac2db(sacfile, last, **tables):
    """
    Get core tables instances from an item.

    Parameters
    ----------
    item : SAC file name
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
    

def manage_ids(session, last, **rows):
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

    args = parser.parse_args(argv)

    session = parse_session(args)

    tables = parse_tables(args)

    files = parse_files(args)

    for table in tables.values():
        table.__table__.create(session.bind, checkfirst=True)

    lastids = ['orid', 'evid', 'chanid', 'wfid', 'arid']
    last = ps.get_lastids(session, tables['lastid'], lastids, create=True)

    for sacfile in files:
        print sacfile

        rows = sac2db(sacfile, last, **tables)

        # manage the ids
        manage_ids(session, last, **rows)

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
