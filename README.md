# Pisces

Pisces is a Python library that connects your geophysical analysis environment
to a SQL database that uses the Center for Seismic Studies (CSS) 3.0 or NNSA KB
Core table schema.

Documentation: <https://lanl-seismoacoustics.github.io/pisces>

Repository: <https://github.com/lanl-seismoacoustics/pisces/>

![Build Status](https://github.com/LANL-Seismoacoustics/pisces/workflows/Python%20package/badge.svg?branch=master)


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
