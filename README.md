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
* C compiler (for optional `e1` dependency)

Install from [PyPI](https://pypi.python.org/pypi):

```
pip install pisces
```

If you use "e1" format data, you also need to install the `e1` package:

```
pip install e1
```

You can install them both at the same time with:

```
pip install pisces[e1]
```


Install current master from GitHub:

```
pip install git+https://github.com/LANL-Seismoacoustics/pisces
```

# Recent History 

([full change log](CHANGELOG.md))

## 0.3.2

* Correct links in setup.py

## 0.3.1

* Pisces no longer requires compiling and installing C extension modules.
* Remove `libconvert` C library, and replace it's only exposed function (`s3tos4`)
  with a NumPy-only version.
* Remove `libecompression` C library, and move it to a separate "e1" package on PyPI.
  It will be installed as an optional dependency by installing with `pip install pisces[e1]`.

## 0.3.0

* Python 3 support!
* No more Python 2 support
* Add the ability to target a database and tables in a config file (see util.load_config).


## 0.2.4

* Change package name to "pisces" instead of "pisces-db"
* Add Antelope Datascope schema/tables.
