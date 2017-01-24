#!/urs/bin/env python

# Ported to Python 3.5.2 on 01/24/17
# by: Jeremy Webster

"""
flatfiles2db.py

Usage: db2db.py mydb

Converts mydb.wfdisc, mydb.origin, etc… CSS3 text files into wfdisc, origin
tables in mydb.sqlite database.

"""

import sys
import glob

import pisces as ps
import pisces.tables.css3 as css3


db = sys.argv[1]

session = ps.db_connect('sqlite:///' + db + '.sqlite')


def fill_table(session, table, Table):
    Table.__table__.create(session.bind, checkfirst=True)
    with open('table', 'r') as f:
        for line in f:
            row = Table.from_string(line)
            session.add(row)
        session.commit()


for table in glob.glob(db + '.*'):
    if table.endswith('origin'):
        fill_table(session, table, css3.Origin)

    if table.endswith('site'):
        fill_table(session, table, css3.Site)

    if table.endswith('wfdisc'):
        fill_table(session, table, css3.Wfdisc)
