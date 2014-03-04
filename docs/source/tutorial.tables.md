# The Database

Learn about the tables, how to create them, and how to make new tables.

---

The Pisces seismic database uses about a dozen core tables to represent station, event, and waveform information.  
It is a SQL database and uses tables defined in the CSS 3.0 seismic schema (and 

## SQL relational databases

Structured Query Language (SQL) is a language standard for operating on relational database tables.
A table is a collection of related columns, and a schema is a set of related tables.



## CSS 3.0 Schema

The Center for Seismic Studies (CSS 3.0) seismic schema is

## NNSA KB Core schema

The National Nuclear Security Administration (NNSA) Knowledge Base Core (KB CORE) tables are 

## SQLAlchemy 

Pisces uses SQLAlchemy and its Object Relational Mapper (ORM) to represent database tables.  

**In the ORM, database tables are Python classes, and rows in a table are instances of that class.**

## Making new tables

You can extend the core schema to use new tables.
Here's we'll reproduce the "ccwfdisc" cross-correlation descriptor table from [http://www.iris.edu/dms/products/ancc-ciei/](), shown here:

![ccwfdisc table](https://raw.github.com/jkmacc-LANL/pisces/master/docs/data/ancc-ciei_table.png "ccwfdisc table")



    import sqlalchemy as sa
    import pisces.schema.css3 as css
    
    # css.Base instructs the table to use Column info dictionaries 
    class Ccwfdisc(css.Base):
        __tablename__ = 'ccwfdisc'
        __table_args__ = (sa.PrimaryKeyConstraint('wfid'), 
                            sa.UniqueConstraint('wfid', 'dir', 'dfile'))
    
        sta1 = css.sta.copy()
        net1 = css.net.copy()
        sta2 = css.sta.copy()
        net2 = css.net.copy()
        chan1 = css.chan.copy()
        chan2 = css.chan.copy()
        time = css.time.copy()
        wfid = css.wfid.copy()
        endtime = css.endtime.copy()
        nsamp = css.nsamp.copy()
        samprate = css.samprate.copy()
        snrn = sa.Column('snrn', sa.Float(24), 
            info={'default': -1.0 ,'parse': float, 'width': 16, 'format': '16.6f')
        snrp = sa.Column('snrp', sa.Float(24), 
            info={'default': -1.0 ,'parse': float, 'width': 16, 'format': '16.6f')
        sdate = sa.Column('sdate', sa.Integer, 
            info={'default': -1 ,'parse': int, 'width': 8, 'format': '8d')
        edate = sa.Column('edate', sa.Integer, 
            info={'default': -1 ,'parse': int, 'width': 8, 'format': '8d')
        stdays = sa.Column('stdays', sa.Integer,
            info={'default': -1, 'parse': int, 'width': 6, 'format': '6d'))
        range = sa.Column('range', sa.Float(24), 
            info={'default': -1.0 ,'parse': float, 'width': 10, 'format': '10.3f')
        tsnorm = sa.Column('tsnorm', sa.Float(53), 
            info={'default': -1.0 ,'parse': float, 'width': 14, 'format': '14.4f')
        datatype = css.datatype.copy()
        dir = css.dir.copy()
        dfile = css.dfile.copy()
        foff = css.foff.copy()
        lddate = css.lddate.copy()
