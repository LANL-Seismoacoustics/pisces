# Pisces

Pisces is a Python library that connects your geophysical analysis environment
to a SQL database that uses the Center for Seismic Studies (CSS) 3.0 or NNSA KB
Core table schema.

Documentation: <http://jkmacc-lanl.github.io/pisces>

Repository: <https://github.com/jkmacc-LANL/pisces>

[![Build Status](https://travis-ci.org/jkmacc-LANL/pisces.svg?branch=master)](https://travis-ci.org/jkmacc-LANL/pisces)
[![Build status](https://ci.appveyor.com/api/projects/status/w36hbk96bw9lmrnr/branch/master?svg=true)](https://ci.appveyor.com/project/jkmacc-LANL/pisces/branch/master)

## Features

* Import/export waveforms directly to/from your database.  
* Build database queries using Python objects and methods
    ([SQLAlchemy](http:/www.sqlalchemy.org)), not by concatenating SQL strings.
* Integration with [ObsPy](http://www.obspy.org).
* Geographic filtering of results.


## Installation

Requires:

* ObsPy
* Click
* C compiler

Install from [PyPI](https://pypi.python.org/pypi):

```
pip install pisces
```

Install current master from GitHub:

```
pip install git+https://github.com/jkmacc-LANL/pisces
```

# Recent History 

([full change log](CHANGELOG.md))

## 0.2.4

* Change package name to "pisces" instead of "pisces-db"
* Add Antelope Datascope schema/tables.
