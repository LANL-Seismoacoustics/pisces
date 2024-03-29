# The Database

Learn about the tables, how to create them, and how to make new tables.

---

## Introduction

Pisces uses relational database tables to represent station, event, and waveform information.
One can think of database tables as a collection of inter-related sheets in an Excel spreadsheet, each holding columns and rows of data.
The specific tables Pisces uses are defined in the Center for Seismic Studies (CSS) 3.0 seismic schema, and implemented in an SQL relational database.

SQL databases are ubiquitous, and describing them in detail is beyond the scope of this tutorial.
For further guidance or tutorials, please consult the [web](https://www.google.com/search?client=opera&q=sql+databases&sourceid=opera&ie=UTF-8&oe=UTF-8).
Before continuing, however, here are two things to remember:

1. **You don't have to write SQL.**

    Pisces uses the [SQLAlchemy](http://www.sqlalchemy.org) package (SQLA) and its [Object Relational Mapper](http://docs.sqlalchemy.org/en/rel_0_9/orm/tutorial.html) to represent database tables.

    > The SQLAlchemy Object Relational Mapper presents a method of associating user-defined Python classes with database tables, and instances of those classes (objects) with rows in their corresponding tables. --<cite>Mike Beyer</cite>, creator SQLAlchemy

    In other words, we can work with familiar Python concepts (classes, instances, and methods) instead of writing SQL (though you can still write SQL if you want).
    This doesn't mean you can _ignore_ the SQL-ness of your database.
    You should understand the concepts, you just don't have to write and manage SQL strings.

2. **You don't have to install a relational database management system (DBMS).**  

    You already have one.
[SQLite](http://www.sqlite.org) is part of the Python Standard Library, and SQLAlchemy is compatible with SQLite.
SQLA is also compatible with [many](http://docs.sqlalchemy.org/en/rel_0_9/dialects/) other database backends, so you could scale up and use Oracle or PostgreSQL if it makes sense for your project, _and you wouldn't have to change your code_.

<!--
Here are some definitions, if you're not familiar with databases.

**Column**
:   A bit of data you want to store, defined by data type (float, string, etc.), range, null/default values, etc.

**Table**
:   A collection of related columns, plus maybe some rules about rows in the table.

**Schema**
:   A collection of related tables and how the tables relate.

**Relational Database**
:   An actual implementation of related tables on a system.

**Structured Query Language (SQL)**
:   A standardized language for querying, joining, and defining database tables.
    It looks like `select * from origin where lat between 100 and 105 and mb > 4.5`.

**Relational Database Management System (RDMS)**
:   The software that executes SQL to work with your database.
    Examples include MySQL, Oracle, PostgreSQL, and SQLite.

Further questions about SQL and relational databases are directed to our [FAQ](https://www.google.com/search?client=opera&q=sql+databases&sourceid=opera&ie=UTF-8&oe=UTF-8).
-->

---

## The core tables

Pisces comes with the 20 prototype tables defined in the CSS 3.0 seismic schema.
These are described in detail in the original specification (Anderson et al., 1990).
Below are the entity-relationship diagrams for the CSS 3.0 schema from Anderson et al. (1990).

<!--
**affiliation**
:   Network station affiliations

**arrival**
:   Summary information on a seismic arrival

**assoc**
:   Data associating arrivals with origins

**event**
:   Event identification

**instrument**
:   Generic (default) calibration information about a station

**lastid**
:   Counter values (Last value used for keys)

**netmag**
:   Network magnitude

**network**
:   Network description and identification

**origerr**
:   Summary of errors in origin estimations

**origin**
:   Data on event location and confidence bounds

**remark**
:   Comments

**sensor**
:   Specific calibration information for physical channels

**site**
:   Station location information

**sitechan**
:   Station-channel information

**sregion**
:   Seismic region

**stamag**
:   Station magnitude

**stassoc**
:   Arrivals from a single station grouped into an event

**wfdisc**
:   Waveform file header and descriptive information

**wftag**
:   Waveform mapping file

**wftape**
:   Waveform tape file header and descriptive information (not generally used)
-->


#### Primary tables

(only primary and unique keys are shown)

![primary tables](../_static/css3_primary.png "primary tables")


#### Lookup tables

(only primary and unique keys are shown)

![lookup tables](../_static/css3_lookup.png "lookup tables")

Anderson, J., Farrell, W. E., Garcia, K., Given, J., and Swanger, H. (1990). Center for Seismic Studies version 3 database: Schema reference manual. Technical Report C90-01, Center for Seismic Studies, 1300 N. 17th Street, Suite 1450, Arlington, Virginia 22209-3871. [PDF (19 MB)](../_static/Anderson1990.pdf)

### The Pisces implementation

Pisces implements CSS 3.0 schema with relatively few constraints:

* Primary keys and unique keys are defined, but foreign keys are not. All joins must be explicit.
* ids (e.g. orid, wfid) are not automatically incremented. You must use a counter and the "lastid" table.
* There are no indexes (internal database structures that speed up queries on certain columns or sets of columns).
* Any column can take an NA value, which will be assigned if not otherwise specified.

This is done to offer users the flexibility to maintain a database to a level of rigor commensurate with the project.
A single-user with a 2-year project database may only ever use the origin, wfdisc, arrival, and assoc tables, and doesn't want to deal with foreign keys,
whereas a multi-user global database may need to populate most/all tables and use consistent ids.
Both are possible.

<!--
In the ORM, **Python classes represent database tables, and instances of that class represent rows in a table.**
-->

---

## Extending the schema

### Defining new tables

The core tables don't describe everything you might care about, such as stacked cross-correlation functions.
Here we'll reproduce the "ccwfdisc" cross-correlation descriptor table from <http://www.iris.edu/dms/products/ancc-ciei/>, which looks like this _(sic)_:

![ccwfdisc table](../_static/ancc-ciei_table.png "ccwfdisc table")

We'll define our new table in a file "mytables.py" by doing the following:

* Import our css3 prototypes into the `css` namespace.
* Inherit from `css.Base`, so that the Ccwfdisc table is a proper SQLAlchemy table, 
  and so that the `info=` dictionaries are used properly in Pisces
* Name the table with `__tablename__`
* Specify the primary and unique constraints with `__table_args__`.
  Each table needs at least a primary key constraint.
* Re-use a number of known columns with `.copy()`
* Define new columns, including the `info` dictionary for Pisces.


#### mytables.py

```python
import sqlalchemy as sa
import pisces.schema.css3 as css

class Ccwfdisc(css.Base):
    __tablename__ = 'ccwfdisc'
    __table_args__ = (sa.PrimaryKeyConstraint('wfid'), 
                        sa.UniqueConstraint('wfid', 'dir', 'dfile'))

    sta1 = css.sta.copy()
    net1 = css.net.copy()
    sta2 = css.sta.copy()
    net2 = css.net.copy()
    chan1 = css.chan.copy()
    chan2 = css.chan.copy()
    time = css.time.copy()
    wfid = css.wfid.copy()
    endtime = css.endtime.copy()
    nsamp = css.nsamp.copy()
    samprate = css.samprate.copy()
    snrn = sa.Column('snrn', sa.Float(24), 
        info={'default': -1.0 ,'parse': float, 'width': 16, 'format': '16.6f')
    snrp = sa.Column('snrp', sa.Float(24), 
        info={'default': -1.0 ,'parse': float, 'width': 16, 'format': '16.6f')
    sdate = sa.Column('sdate', sa.Integer, 
        info={'default': -1 ,'parse': int, 'width': 8, 'format': '8d')
    edate = sa.Column('edate', sa.Integer, 
        info={'default': -1 ,'parse': int, 'width': 8, 'format': '8d')
    stdays = sa.Column('stdays', sa.Integer,
        info={'default': -1, 'parse': int, 'width': 6, 'format': '6d'))
    range = sa.Column('range', sa.Float(24), 
        info={'default': -1.0 ,'parse': float, 'width': 10, 'format': '10.3f')
    tsnorm = sa.Column('tsnorm', sa.Float(53), 
        info={'default': -1.0 ,'parse': float, 'width': 14, 'format': '14.4f')
    datatype = css.datatype.copy()
    dir = css.dir.copy()
    dfile = css.dfile.copy()
    foff = css.foff.copy()
    lddate = css.lddate.copy()
```

### Column info

The `info` dictionary for each column needs the following entries, at minimum:

* `default`: The value used for the column when it is otherwise not specified.
* `parse`: A callable that accepts the fixed-width string and returns the right type for the database.
* `format`: The column's external format, from the Python [string format specification mini-language](http://docs.python.org/2/library/string.html#format-specification-mini-language).

There are some differences between the Fortran-style "external format" and those used by Python.
In Python, the type characters may be different from Fortran, and they always follow the width.
See the following table for a few examples:

Description        | Fortran   | Python
:----------------- | :-------: | :------:
6-character string | `a6`      | `6.6s`
8-digit integer    | `i8`      | `8d`


### Create a table
To create the table in a database, just use SQLAlchemy syntax:

```python
import sqlalchemy as sa
from mytables import Ccwfdisc

engine = sa.create_engine('sqlite:///mydatabase.sqlite')

Ccwfdisc.__table__.create(engine)
```

For every ORM class, there is a hidden `__table__` object that has a `create` method.
This method accepts an [Engine](http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html) instance that points to a specific database, where it will be created.

### Defining new prototype tables

You can use the previous table with any database, as long as the table will be called "ccwfdisc".
If you want to re-use this table structure across multiple table names without having to repeat the previous definition each time, you'll need to define a new *prototype table* ([abstract table](http://docs.sqlalchemy.org/en/rel_0_8/orm/extensions/declarative.html#abstract) in SQLAlchemy).

This is how the "ccwfdisc" table would be defined, as a new prototype.

#### mytables_abs.py

```python
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
import pisces.schema.css3 as css

class Ccwfdisc(css.Base):
    __abstract__ = True

    @declared_attr
    def __table_args__(cls):
        return  (sa.PrimaryKeyConstraint('wfid'), 
                    sa.UniqueConstraint('wfid', 'dir', 'dfile'))

    sta1 = css.sta.copy()
    net1 = css.net.copy()
    sta2 = css.sta.copy()
    net2 = css.net.copy()
    chan1 = css.chan.copy()
    chan2 = css.chan.copy()
    time = css.time.copy()
    wfid = css.wfid.copy()
    endtime = css.endtime.copy()
    nsamp = css.nsamp.copy()
    samprate = css.samprate.copy()
    snrn = sa.Column('snrn', sa.Float(24), 
        info={'default': -1.0 ,'parse': float, 'width': 16, 'format': '16.6f')
    snrp = sa.Column('snrp', sa.Float(24), 
        info={'default': -1.0 ,'parse': float, 'width': 16, 'format': '16.6f')
    sdate = sa.Column('sdate', sa.Integer, 
        info={'default': -1 ,'parse': int, 'width': 8, 'format': '8d')
    edate = sa.Column('edate', sa.Integer, 
        info={'default': -1 ,'parse': int, 'width': 8, 'format': '8d')
    stdays = sa.Column('stdays', sa.Integer,
        info={'default': -1, 'parse': int, 'width': 6, 'format': '6d'))
    range = sa.Column('range', sa.Float(24), 
        info={'default': -1.0 ,'parse': float, 'width': 10, 'format': '10.3f')
    tsnorm = sa.Column('tsnorm', sa.Float(53), 
        info={'default': -1.0 ,'parse': float, 'width': 14, 'format': '14.4f')
    datatype = css.datatype.copy()
    dir = css.dir.copy()
    dfile = css.dfile.copy()
    foff = css.foff.copy()
    lddate = css.lddate.copy()
```

The differences are minor:

* use `__abstract__ = True` instead of assigning a `__tablename__`
* use the `@declared_attr` decorator with a `__table_args__` _function_ that _returns_ the constraint tuple.

And this is how the prototype would be implemented and re-used in two different tables, 'ccwfdisc' and 'TA_ccwfdisc'.

#### mytables2.py

```python
import mytables_abs as ab

class Ccwfdisc(ab.Ccwfdisc):
    __tablename__ = 'ccwfdisc'

class TA_Ccwfdisc(ab.Ccwfdisc):
    __tablename__ = 'TA_ccwfdisc'
```

These two tables look the same, have different names, and can reside in the same database.
