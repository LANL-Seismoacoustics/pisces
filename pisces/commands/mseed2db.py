"""
Module for creating wfdisc rows from miniSEED files.

"""
import os

from pisces.util import get_lastids, url_connect
from .util import get_or_create_tables, dicts2rows

def main(session, files=None, file_list=None, absolute_paths=False):
    """
    session : SQLAlchemy.orm.Session instance
    tables : list
        Canonical names for desired database tables.
    prefix : str
        Target core tables using 'account.prefix' naming.
    absolute_paths : bool

    """
    if file_list:
        files = get_files(file_list)
    else:
        files = files

    tables = get_or_create_tables(session, create=True)

    lastids = ['arid', 'chanid', 'evid', 'orid', 'wfid']
    last = get_lastids(session, tables['lastid'], lastids, create=True)

    for msfile in files:
        print(msfile)

        # row_dicts = get_row_dicts(item)

        st = read(msfile, format='MSEED', details=True, headonly=True)
        # a single miniSEED file may be multiple traces.  we need to identify the
        # file offsets (bytes) to each trace.  Traces are added to the Stream in
        # order, with enough header information to calculate that.
        foff = 0
        for tr in st:
            dicts = mseed.mseedhdr2tables(tr.stats, wfdisc=tables['wfdisc'],
                                          site=tables['site'], sitechan=tables['sitechan'])

            foff += tr.stats.mseed.number_of_records * tr.stats.mseed.record_length
            dicts['wfdisc'][0].foff = foff
            dicts['wfdisc'][0].dfile = os.path.basename(msfile)
            
            if absolute_paths:
                idir = os.path.dirname(os.path.realpath(msfile))
            else:
                idir = os.path.dirname(msfile)
                # make sure relative paths are non-empty
                if idir == '':
                   idir = '.'
            dicts['wfdisc'][0].dir = idir

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