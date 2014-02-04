# Pisces

A practical seismological database library in Python.

### Motivation

Relational databases can help seismologists manage data and facilitate research, but ...

* Researchers don't want to learn a separate data-management language, like SQL.  
* Existing seismological database solutions are closed-source, cost money, or have a small/niche user base.

### Goals

* **Let users manage and analyze data in a single language: Python.**  
* **Take advantage of existing widely-used open-source technologies.**  
    * SQL relational databases
    * [Python](http://www.python.org)
    * [SQLAlchemy](http://www.sqlalchemy.org)
    * The [SciPy stack](http://www.scipy.org/about.html) and [ObsPy](http://www.obspy.org)
* **Make data management code extensible, portable, and scalable.**  
  Write code that will not eventually have to be abandoned due to project size, system architecture, or budgetary or licensing concerns.

## Features

* Get waveforms directly from your database.
* Integration with [ObsPy](www.obspy.org).
* Build database queries using Pythonic syntax.
* Free software: LANL-MIT license
* Easy importing/exporting of text "flat-file" data tables.

## What does it look like?

### Define tables

Name your Center for Seismic Studies (CSS) 3.0 tables in a module (e.g. mytables.py),
inheriting structure and constraints.
This just needs to be done once per table name.


    # mytables.py 
    import pisces.schema.css3 as css
    
    class Affiliation(css.Affiliation):
        __tablename__ = 'affiliation'
    
    class Site(css.Site):
        __tablename__ = 'site'
    
    class Origin(css.Origin):
        __tablename__ = 'origin'
    
    class Wfdisc(css.Wfdisc):
        __tablename__ = 'Wfdisc'

### Import and query tables


    import pisces as ps
    import pisces.request as req

    # import your tables
    from mytables import Site, Origin
    from mytables import Affiliation as Affil

    # connect with an existing SQLite database file
    session = ps.db_connect('sqlite:///mydb.sqlite')
    
    # query all stations from the CREST seismic deployment, using SQLAlchemy
    q = session.query(Site).filter(Site.ondate.between(2008001, 2008365))
    csites = q.filter(Site.sta == Affil.sta).filter(Affil.net == 'XP').all()
    
    # query for western US earthquakes, using a Pisces query builder
    wus_quakes = req.get_events(session, Origin, region=(-115, -105, 35, 45), mag={'mb': (4, None)})
    
    # add Albuquerque ANMO to the site table, 
    # and the Chelyabinsk bolide to the origin table
    ANMO = Site(sta='ANMO', lat=34.9459, lon=-106.4572, elev=1.85)
    bolide = Origin(orid=1, lat=55.15, lon=61.41, mb=2.7, etype='xm')
    session.add_all([ANMO, bolide])
    session.commit()
    
    # edit a Site, delete an Origin
    session.query(Site).filter(Site.sta == 'MK31').update({'lat': 42.5})
    session.query(Origin).filter(Origin.orid = 1001).delete()
    session.commit()
    session.close()

### Get a waveform 

...as an ObsPy [Trace object](http://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.html#obspy.core.trace.Trace).

    from mytables import Wfdisc  
    wf = session.query(Wfdisc).filter(Wfdisc.sta == 'ANMO').first()  
    tr = wf.to_trace()  
    tr.plot()  

![ANMO waveform](https://raw.github.com/jkmacc-LANL/pisces/master/docs/data/ANMO.png "ANMO waveform")

