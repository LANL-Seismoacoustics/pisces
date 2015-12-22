# Changelog

## 0.2

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
