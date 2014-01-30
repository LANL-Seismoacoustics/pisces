# Pisces

A practical seismological database library in Python.

## Features

* Get waveforms directly from your database.
* Integration with [ObsPy](www.obspy.org).
* Build database queries using Pythonic syntax.
* Free software: LANL-MIT license
* Easy importing/exporting of text "flat-file" data tables.

Code: [http://github.com/jkmacc-LANL/pisces]()  
Documentation: [http://pisces.rtfd.org]()


## What does it look like?

Name your Center for Seismic Studies (CSS) 3.0 tables in a module:

```python
# mytables.py
import pisces.schema.css3 as css

# assign name, inherit structure and constraints from known CSS 3.0 tables
class Affiliation(css.Affiliation):
    __tablename__ = 'affiliation'

class Site(css.Site):
    __tablename__ = 'site'

class Origin(css.Origin):
    __tablename__ = 'origin'

class Wfdisc(css.Wfdisc):
    __tablename__ = 'Wfdisc'
```

Import and query them in a script:

```python
import pisces as ps
import pisces.request as req
from mytables import Affiliation, Site, Origin

# connect with an existing SQLite database file
session = ps.db_connect('sqlite:///mydb.sqlite')

# load the SQL internals of Affiliation from the database itself
Affiliation.prepare(session.bind)

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
```

Get a waveform (as an ObsPy [Trace object](http://docs.obspy.org/packages/autogen/obspy.core.trace.Trace.html#obspy.core.trace.Trace)).

```python
wf = session.query(Wfdisc).filter(Wfdisc.sta == 'ANMO').first()
tr = wf.to_trace()
tr.plot()
```

![ANMO waveform](http://github.com/jkmacc-LANL/pisces/ANMO.png, "ANMO waveform")

## Motivation

As the volume of seismological data grows, data management becomes more important, and has the potential to hinder research.
Relational databases have long existed to help with this problem, but they have not been widely adopted for several broad reasons:

* **Researchers don't want to learn a separate data management language, like SQL.**  
  They are more likely to string together tools they already know, like shell scripts and file-based "databases."
* **Existing seismological database solutions are difficult to learn.**  
  Some existing solutions have expensive or restrictive licenses, do not expose source code, and/or have a small/niche user base.  

## Design Goals

We introduce Pisces, with the following design goals in mind:

* **Let users manage and analyze data in a single language.**  
  Python and scientific Python ecosystem (the "[SciPy stack](http://www.scipy.org/about.html)") are an increasingly desirable research environment.
  We wish to more seamlessly integrate good data management (relational databases) and data analysis.
* **Take advantage of existing widely-used open-source technologies.**  
  These include [Python](www.python.org), [SQLAlchemy](www.sqlalchemy.org), the SciPy stack, and SQL relational databases.
  These are free and widely-used technologies, allowing researchers to leverage a wide knowledge base for writing and troubleshooting data management code.
* **Make data management code extensible, portable, and scalable.**  
  Even in the span of just a few years, a researcher may encounter many different projects, system architectures, or budgetary and licensing concerns.
  Python and SQLAlchemy make it possible to write code that will will not eventually have to be abandoned due to any one of these concerns. 
  Code written for a small project that uses [SQLite](www.sqlite.org) on a Mac will also work for a large project using a remote Oracle database on a Linux system.



<!---
.. image:: https://badge.fury.io/py/pisces.png
    :target: http://badge.fury.io/py/pisces
    
.. image:: https://travis-ci.org/jkmacc-LANL/pisces.png?branch=master
        :target: https://travis-ci.org/jkmacc-LANL/pisces

.. image:: https://pypip.in/d/pisces/badge.png
        :target: https://crate.io/packages/pisces?version=latest
-->



