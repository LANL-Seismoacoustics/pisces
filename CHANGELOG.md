# Changelog

## next


## 0.2.2

### Changes

* Windows support!  Thanks to @mitchburnett!  e1 and convert C libraries now
  build (using MSVC).
* Automated testing on Mac OSX, Linux, and Windows 7, for Python 2.7 and 3.4,
  thanks to Travis CI and Appveyor.


## 0.2.1

### Bug fixes

* Default `wdisc.calib` value is 1, not -1.
* `foff` value in `sac2db` is 632 instead of 634 (Issue #12)
* `dir` entry in `sac2db` will be `.` instead of empty if relative paths are
   requested. (Issue #11)


## 0.2.0

### New Features

* Add new command-line interface, `pisces`, which offers the `sac2db` and
  `mseed2db` subcommands, for building a database from a collection of files.

### Changes

* Add Click library as a dependency, to support new command line interface.
* Bump the required SQLAlchemy version to at least 0.9.

### Bug fixes

* Fix "s3" datatype conversion on little-endian architectures (Issue #9).
* Allow Python protected keywords to be used as column names (Issue #4).
* Fix string stripping in `pisces/io/sac.py`
