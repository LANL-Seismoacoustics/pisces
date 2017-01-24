#!/usr/bin/env python
"""
Command line script accepts a file name, filename regex, or list of file
names, and produces a kbcore database from header information therein.  Parses
trace header information as read by obspy.core read function (which depends on
obspy.io.sac, obspy.io.mseed, ect...).

April 14, 2015, OM

"""
import sys
import glob
import os

from optparse import OptionParser

import pisces as ps

import pisces.schema.kbcore as kb
import pisces.io.sac as sac

from sqlalchemy.exc import NoSuchTableError, IntegrityError, OperationalError
from sqlalchemy.orm.exc import UnmappedInstanceError
from obspy.core import read, AttribDict

# -------------------------------------------------------------
#
#                 HELPER FUNCTIONS


def split_slash(option, opt_str, value, parser):
    setattr(parser.values, option.dest, [float(val) for val in value.split("/")])


def split_comma(option, opt_str, value, parser):
    setattr(parser.values, option.dest, [val.strip() for val in value.split(",")])


def expand_glob(option, opt_str, value, parser):
    """Returns an iglob iterator for file iteration. Good for large file lists."""
    setattr(parser.values, option.dest, glob.iglob(value))


# functions that produce sqlalchemy.orm table instances from obspy traces
# return empty instances if no useful header info is found
# only these tables will be written in the output database
# TODO: optionally, provide a class to return a filled instance of that class?
mapfns = {'affiliation': sac.tr2affiliation,
          'arrival': sac.tr2arrival,
          'assoc': sac.tr2assoc,
          'event': sac.tr2event,
          'instrument': sac.tr2instrument,
          'origin': sac.tr2origin,
          'site': sac.tr2site,
          'sitechan': sac.tr2sitechan,
          'wfdisc': sac.tr2wfdisc}

PROTOTYPES = {'affiliation': kb.Affiliation,
              'arrival': kb.Arrival,
              'assoc': kb.Assoc,
              'event': kb.Event,
              'instrument': kb.Instrument,
              'lastid': kb.Lastid,
              'origin': kb.Origin,
              'site': kb.Site,
              'sitechan': kb.Sitechan,
              'wfdisc': kb.Wfdisc}

# TODO: refactor parts of main into db.util.traces2db
# TODO: factor out parts for updating a database, gear only towards writing
#       fresh tables


def reflect_or_create_tables(options):
    """
    returns a dict of classes
     make 'em if they don't exist
     "tables" is {'wfdisc': mapped table class, ...}
     """
    tables = {}
    # this list should mirror the command line table options
    for table in mapfns.keys() + ['lastid']:
        # if options.all_tables:
        fulltabnm = getattr(options, table, None)
        if fulltabnm:
            try:
                tables[table] = ps.get_tables(session.bind, [fulltabnm])[0]
            except NoSuchTableError:
                print "{0} doesn't exist. Adding it.".format(fulltabnm)
                tables[table] = ps.make_table(fulltabnm, PROTOTYPES[table])
                tables[table].__table__.create(session.bind, checkfirst=True)

    return tables


def get_file_iterator(options):
    """
    returns a sequence of files
    raises IOError if problemmatic
    raises ValueError if problemmatic
    """
    # --------  BUILD FILE ITERATOR/GENERATOR --------
    if options.f is not None:
        files = options.f
    elif options.l is not None:
        try:
            lfile = open(options.l, 'r')
            # make a generator of non-blank lines
            files = (line.strip() for line in lfile if line.strip())
        except IOError:
            msg = "{0} does not exist.".format(options.l)
            raise IOError(msg)
    else:
        msg = "Must provide input files or file list."
        raise ValueError(msg)

    return files

# ---------------- MAIN --------------- #


def main(argv=None):
    """If imported, use with this syntax:
    >>> from traces2db import main
    >>> main(['-f','*.sac','dbout'])

    Returns exit_code
    """
    if argv is None:
        argv = sys.argv

    exit_code = 0

    try:
        parser = OptionParser(usage="Usage: %prog [options] ",
                              description="""Write data from sac or mseed headers into a database. Currently, only SAC files are supported.""",
                              version='0.1')
        parser.add_option('-f', '--files',
                          default=None,
                          help="Unix-style file name expansion for trace files.",
                          type='string',
                          action="callback",
                          callback=expand_glob,
                          dest='f')
        parser.add_option('-l', '--list',
                          default=None,
                          help="A text file containing a column of trace file names.",
                          type='string',
                          dest='l')
        parser.add_option('-t', '--tables',
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
                          dest='rel_path')
#        parser.add_option('-t','--type',
#                default=None,
#                help="File type: 'SAC' or 'MSEED'",
#                type='string',
#                dest='t')
#        parser.add_option('--db',
#                help="Also return formatted flat files.",
#                default=False,
#                action='store_true',
#                dest='db')

        options, args = parser.parse_args(argv)

        if len(args) > 1:
            """Unknown positional arguments given."""
            print parser.print_help()
            exit_code = 1
        else:
            # -------- MAKE CONNECTIONS --------
            if options.gndd:
                # TODO: add a password option here
                try:
                    from pisces_gndd import gndd_connect
                    session = gndd_connect(options.user)
                except ImportError as e:
                    raise e
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

            tables = reflect_or_create_tables(options)

            try:
                files = get_file_iterator(options)
            except IOError as e:
                # file list doesn't exist
                raise e
                exit_code = 1
            except ValueError:
                # input neither a file list nor input files
                print parser.print_help()
                exit_code = 1

            if exit_code != 1:

                # -------- GET ALL IDS --------
                # "last" is a dict of initialized id generators.
                # use it like last.arid.next()
                # update lastid table after file loop!
                # XXX: experimental!
                lastid = tables['lastid']
                last = AttribDict(db.util.get_id_gen(['arid', 'orid', 'evid',
                                                     'wfid', 'chanid', 'inid'],
                                                     session, lastid))
#                last = AttribDict()
#                #pdb.set_trace()
#                for iid in ['arid', 'orid', 'evid', 'wfid', 'chanid', 'inid']:
#                    try:
#                        val = session.query(lastid.keyvalue).filter(lastid.keyname == iid).one()[0]
#                    except NoResultFound:
#                        # no id.  make one, starting at zero
#                        val = 0
#                    last[iid] = db.gen_id(val)

                # requested tables, minus lastid
                core_tabs = tables.keys()[:]
                core_tabs.remove('lastid')
                # -------- ITERATE OVER FILES --------
                for ifile in files:
                    print ifile
                    try:
                        tr = read(ifile, headonly=True)[0]
                        trtables = db.trace2tables(tr, tables=core_tabs)
                        # trtables is {'site': mapped instance, ...} for all
                        # tables requested or available from header

                        # FILL IN AUTOMATICALLY GENERATED TABLES
                        # TODO: this section needs better logic, talk to Richard
                        # combine session.add(_all), session.commit,
                        # exception catching with id management.

                        affil = trtables.get('affiliation')
                        arrivals = trtables.get('arrival')
                        site = trtables.get('site')
                        sitechan = trtables.get('sitechan')
                        instrument = trtables.get('instrument')
                        assocs = trtables.get('assoc')
                        event = trtables.get('event')
                        origin = trtables.get('origin')
                        wfdisc = trtables.get('wfdisc')

                        # FILL IN IDs AND OTHER IMPORTANT VALUES

                        # if affil:
                        #    # affiliation.ontime
                        #    pass

                        if arrivals:
                            # arrival.arid
                            for arrival in arrivals:
                                if not arrival.arid:
                                    arrival.arid = last.arid.next()
                        if origin:
                            # origin.orid
                            if not origin.orid:
                                # XXX: always increments orid.
                                # combine with table add logic
                                origin.orid = last.orid.next()

                        if assocs and arrivals:
                            # assoc.arid
                            # assoc.orid
                            # XXX: assumes arrivals are related to origin
                            # and assocs and arrivals are in the same order
                            for (assoc, arrival) in zip(assocs, arrivals):
                                assoc.arid = arrival.arid
                                if hasattr(origin, 'orid'):
                                    assoc.orid = origin.orid
                        # if site:
                        # always gonna be a site, right?
                        #     site.ondate
                        #     pass

                        if sitechan:
                            # sitechan.ondate
                            # sitechan.chanid
                            if not sitechan.chanid:
                                sitechan.chanid = last.chanid.next()

                        # if instrument:
                        #    # instrument.inid
                        #    # instrument.dir
                        #    # instrument.dfile
                        #    # instrument.rsptype
                        #    pass

                        if wfdisc:
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

                        # -------- ADD TABLES TO DATABASE --------

                        for tableval in trtables.values():
                            if tableval:
                                try:
                                    session.add(tableval)
                                    session.commit()
                                except UnmappedInstanceError:
                                    # tableval was a list. i.e. arrival or assoc
                                    # may need some IntegrityError catching here
                                    session.rollback()
                                    # XXX: is add_all what I mean to do here?
                                    session.add_all(tableval)
                                except IntegrityError as e:
                                    # duplicate or nonexistant primary/unique keys
                                    # TODO: make this more descriptive
                                    print " Duplicate row in {0}".format(tableval.__table__.name)
                                    session.rollback()
                                except OperationalError as e:
                                    # no such table name.  shouldn't happen.
                                    # database is locked.
                                    session.rollback()
                                    raise e
                                # except InvalidRequestError:
                                #    #XXX: what is this error?
                                #    #maybe tried to insert None
                                #    session.rollback()

                    except (IOError, TypeError):
                        # can't read file or doesn't exist.
                        print "Couldn't read file {0}.".format(ifile)

                # close list file here
                if options.l:
                    lfile.close()

                # update lastid table
                # XXX: experimental!
                db.util.update_ids(session, lastid, **last)
#                for iid in ['arid', 'orid', 'evid', 'wfid', 'chanid', 'inid']:
#                    try:
#                        idrow = session.query(lastid).filter(lastid.keyname == iid).one()
#                        idrow.keyvalue = last.get(iid).next() - 1
#                    except NoResultFound:
#                        #lastid table doesn't have this id
#                        idrow = tables['lastid'](keyname=iid,
#                                                 keyvalue=last.get(iid).next()-1)
#                    session.merge(idrow)
#                session.commit()

    except SystemError as e:
        # TODO: why this error?
        exit_code = e.code

    return exit_code


# ----------- run only if called from the shell ------------------#
if __name__ == "__main__":
    """If executed from the shell, get options and defaults there, then run
    program."""
    exit_code = main(sys.argv)

    if exit_code == 0:
        # do some stuff here?
        pass

    sys.exit(exit_code)
