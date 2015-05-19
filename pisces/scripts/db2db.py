import glob

import pisces as ps
import pisces.tables.css3 as css3

db = 'mydb'

session = ps.db_connect('sqlite:///path/to/' + db + '.sqlite')

def stuff_table(session, table, Table):
    with open('table', 'r') as f:
        for line in f:
            row = Table.from_string(line)
            session.add(row)
        session.commit()

for table in glob.glob(db + '.*'):
    if table.endswith('origin'):
        stuff_table(session, table, css3.Origin)

    if table.endswith('site'):
        stuff_table(session, table, css3.Site)

    if table.endswith('wfdisc'):
        stuff_table(session, table, css3.Wfdisc)
