# Pisces

A practical seismological database library in Python.

---

Pisces connects your Python analysis environment to a seismological database.

**Manage and analyze data in the same language**  
Don't use separate data-management language, like SQL or shell scripts. Just use Python, and connect to [SciPy](http://www.scipy.org/about.html), [ObsPy](http://www.obspy.org), [AIMBAT](http://www.earth.northwestern.edu/~xlou/aimbat.html), [pyTDMT](http://webservices.rm.ingv.it/pyTDMT/), [StreamPick](https://github.com/miili/StreamPick), and the rest of the scientific Python ecosystem.

**Use common open-source technologies and standards**  
SQL relational databases, [Python](http://www.python.org), [SQLAlchemy](http://www.sqlalchemy.org), and the [SciPy stack](http://www.scipy.org/about.html) are widely-used, free, and open-source technologies.
Because of this, you can leverage knowledge from sites, like [StackOverflow](http://stackoverflow.com/search?q=sqlalchemy), and other disciplines, like web development, for database examples, troubleshooting, or tricks.

**Write portable, extensible, and scalable code**  
Python is multi-platform, SQLAlchemy is database-agnostic, and the whole stack is free and open-source.  Write code that will not eventually have to be abandoned due to project size, system architecture, or budgetary or licensing concerns.


## Features

* Import/export waveforms directly to/from your database.
* Easy importing/exporting of text "flat-file" data tables.
* Build database queries using Python objects and methods ([SQLAlchemy](http://www.sqlalchemy.org)), not by concatenating SQL strings.
* Integration with [ObsPy](http://www.obspy.org).
* Geographic filtering of results.


```{toctree}
:hidden: true

Home <self>
overview.md
quickstart.md
```

```{toctree}
:hidden: true
:caption: Tutorials
:maxdepth: 2

tutorial/tables.md
tutorial/queries.md
tutorial/waveforms.md
tutorial/flatfiles.md
```


```{toctree}
:hidden: true
:maxdepth: 2
:caption: Reference

about/license.md
about/roadmap.md
apidocs/index
```
<!-- about/changelog.md -->
