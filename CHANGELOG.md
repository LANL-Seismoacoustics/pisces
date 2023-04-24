# Change Log

## master/main


## 0.4.1

* Drop testing on Python 3.6, add 3.9 and 3.10
* Drop AppVeyor for testing on Windows, use GitHub Actions instead
* The unimplemented `stime` keyword in `pisces.request.get_stations` has been replaced
  with `time_span`, which accepts time ranges as YYYYddd julian dates.
* Fixed typo in `pisces.request.get_stations` implementation of `nets` keyword.
* New handling of wildcards in `pisces.request.get_stations`
* Fixed typo in `pisces.request.get_stations` implementation of `channels` keyword.
* Fixed typo in `pisces.requests.wfdisc_rows_to_stream` 😳 Yikes!
* New contributor Samuel Chodur!
* Use GitHub Actions for wheels and releases to PyPI
* Add `asquery` option to `pisces.request.get_waveforms`

## 0.4.0
* Bump required SQLAlchemy version to add least 1.4
* Updated import locations of `sqlalchemy.ext.declarative.api` functions to `sqlalchemy.orm`
* Changed the `Column.copy()` method to `Column._copy()` in `pisces.schema.antelope.py`, 
  `pisces.schema.css3.py`, and `pisces.schema.kbcore.py`.  This remove deprecation warnings.

## 0.3.2

* fix bug in `io.readwaveform.read_s3` where too many return values were expected. (Issue #46)
* `wftag` now parsed as a float instead of an integer in KB Core and CSS3 schemas
* `Wftag` primary keys are `tagname`, `tagid`, and `wfid` instead of just `tagid`

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

## 0.2.2

### Changes

* `pisces.util.get_tables`, `pisces.util.make_tables`, and
  `pisces.util.get_or_create_tables` are deprecated and will raise a warning.
* `pisces.request.get_waveforms` now has a `tol` keyword that will raise an
  exception if any returned waveform is not within `tol` seconds from the
  requested starttime/endtime.
* Added `--bbfk` flag to `pisces sac2db`, which uses the broadband f-k (BBFK)
  convention of reading x, y array offset distances in the USER 7, 8 SAC
  header variables and storing them Site.dnorth and Site.deast.
* Windows support!  Thanks to @mitchburnett!  e1 and convert C libraries now
  build (using MSVC).
* Automated testing on Mac OSX, Linux, and Windows 7, for Python 2.7 and 3.4,
  thanks to Travis CI and Appveyor.
* Require ObsPy > 1.0

### Bug fixes

* Fixed sac2db wfdisc.foff (issue #12) and wfdisc.dir (issue #11) handling.


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
