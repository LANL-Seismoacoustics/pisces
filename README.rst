Pisces
======

Pisces is a practical seismological database library in Python.
Connect your Python analysis environment to a seismological database, without having to use a separate data-management language, like SQL or shell scripts.
Pisces uses common open-source technologies and standards, and allows you to write portable, extensible, and scalable code.

Documentation: http://jkmacc-lanl.github.io/pisces

Repository: https://github.com/jkmacc-LANL/pisces

--------------

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


|Analytics|

.. |Analytics| image:: https://ga-beacon.appspot.com/UA-48246702-1/pisces/readme
   :target: https://github.com/igrigorik/ga-beacon

