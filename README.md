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

## Introduction

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



