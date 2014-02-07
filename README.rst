Pisces
======

A practical seismological database library in Python.

--------------

Overview
--------

Pisces connects your Python analysis environment to a seismological
database.

**Manage and analyze data in the same language**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Don't use separate data-management language, like SQL or shell scripts.
Just use Python, and connect to
`SciPy <http://www.scipy.org/about.html>`__,
`ObsPy <http://www.obspy.org>`__,
`AIMBAT <http://www.earth.northwestern.edu/~xlou/aimbat.html>`__,
`pyTDMT <http://webservices.rm.ingv.it/pyTDMT/>`__,
`StreamPick <https://github.com/miili/StreamPick>`__, or one of the many
other useful analysis packages in the scientific Python ecosystem.

**Use common open-source technologies and standards**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

| SQL relational databases, `Python <http://www.python.org>`__,
`SQLAlchemy <http://www.sqlalchemy.org>`__, and the `SciPy
stack <http://www.scipy.org/about.html>`__ are widely-used, free, and
open-source technologies.
| Because of this, you can leverage knowledge from sites, like
StackOverflow, and other disciplines, like web development, for database
examples, troubleshooting, or tricks.

**Write portable, extensible, and scalable code**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Python is multi-platform, SQLAlchemy is database-agnostic, and the whole
stack is free and open-source. Write code that will not eventually have
to be abandoned due to project size, system architecture, or budgetary
or licensing concerns.

Features
~~~~~~~~

-  Import/export waveforms directly to/from your database.
-  Easy importing/exporting of text "flat-file" data tables.
-  Build database queries using Python objects and methods
   (`SQLAlchemy <http:/www.sqlalchemy.org>`__), not by concatenating SQL
   strings.
-  Integration with `ObsPy <http://www.obspy.org>`__.
-  Geographic filtering of results.

--------------

`Documentation: <http://jkmacc-LANL.github.io/pisces>`__

`Repository: <http://github.com/jkmacc-LANL/pisces>`__

--------------

Installation
------------

Requires:

-  NumPy
-  ObsPy
-  SQLAlchemy>0.7
-  C, Fortran compiler

Install from `PyPI <https://pypi.python.org/pypi>`__:

::

    pip install pisces-db

Install current master from GitHub:

::

    pip install git+https://github.com/jkmacc-LANL/pisces

