"""
Module for creating wfdisc rows from miniSEED files.

"""
import os

from obspy import read
import sqlalchemy.exc as exc

from pisces.util import get_lastids, url_connect
from .util import get_or_create_tables, dicts2rows, get_files
import pisces.io.mseed as mseed

def make_atomic(last, **rows):
    """
    Unify related table instances/row, including: ids, dir, and dfile

    Parameters
    ----------
    last : obspy.AttributeDict
        {'keyvalue': lastid instance, ...}
    rows : dict
        {'canonical tablename': [list of row instances], ...}
        These row instances are related.

    """ 
    for wfdisc in rows.get('wfdisc', []):
        wfdisc.wfid = next(last.wfid)
    
    for sitechan in rows.get('sitechan', []):
        # XXX: this is wrong, as each new sitechan doesn't automatically get a
        # new chanid, but we accept this for now, since duplicate sitechans
        # will be rejected upon database write.
        sitechan.chanid = next(last.chanid)


def main(session, files=None, file_list=None, prefix=None, absolute_paths=False):
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

    tables = get_or_create_tables(session, prefix=prefix, create=True)

    lastids = ['chanid', 'wfid']
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
            rows = mseed.mseedhdr2tables(tr.stats, wfdisc=tables['wfdisc'],
                                         site=tables['site'], sitechan=tables['sitechan'],
                                         affiliation=tables['affiliation'])

            foff += tr.stats.mseed.number_of_records * tr.stats.mseed.record_length
            rows['wfdisc'][0].foff = foff
            rows['wfdisc'][0].dfile = os.path.basename(msfile)
            
            if absolute_paths:
                idir = os.path.dirname(os.path.realpath(msfile))
            else:
                idir = os.path.dirname(msfile)
                # make sure relative paths are non-empty
                if idir == '':
                   idir = '.'
            rows['wfdisc'][0].dir = idir

            # manage the ids
            make_atomic(last, **rows)

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