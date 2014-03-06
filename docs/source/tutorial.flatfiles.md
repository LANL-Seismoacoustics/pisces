# Import/Export Flat Files

Easily go between database objects and text files.

---


## Import

Many times, database tables are represented as fixed-format text files. 
Pisces makes it easy to go between database objects and these external flat file representations.

Here, we'll import the following KB Core Site flat file, "TA.site".
Each line in the text file is passed to `Site.from_string`, which is a 
Pisces-specific method that uses the underlying column descriptions to interpret 
fields in the flat file row string into a Site row instance. 
Finally, `session.add(isite)` and `session.commit()` add and write rows to the 
database.

#### TA.site

    K02A         -1  2286324   42.766700 -123.489800    0.9630 Glendale, Oregon,U.S.A.                            ss   K02A      0.0000    0.0000 2009-04-15 15:55:50
    I03D    2009307  2286324   43.697200 -123.348700    0.1400 Drain, OR, USA                                     ss   I03D      0.0000    0.0000 2011-10-11 13:07:17
    P01C         -1  2286324   39.469000 -123.337500    0.4409 Double 8 Ranch, Willits, California,U.S.A.         ss   P01C      0.0000    0.0000 2009-04-15 15:55:50
    N02C         -1  2286324   40.822000 -123.305700    0.7170 Big Bar, California,U.S.A.                         ss   N02C      0.0000    0.0000 2009-04-15 15:55:50
    H03A         -1  2286324   44.676500 -123.292300    0.2143 Soap Creek Ranch, Albany, Oregon,U.S.A.            ss   H03A      0.0000    0.0000 2009-04-15 15:55:50
    G03A         -1  2286324   45.315300 -123.281100    0.2080 Yamhill, Oregon,U.S.A.                             ss   G03A      0.0000    0.0000 2009-04-15 15:55:50
    I03A         -1  2286324   43.972600 -123.277700    0.2057 Eugene, Oregon,U.S.A.                              ss   I03A      0.0000    0.0000 2009-04-15 15:55:50
    G03D    2009297  2286324   45.211500 -123.264100    0.2220 McMinnville, OR, USA                               ss   G03D      0.0000    0.0000 2011-10-11 13:07:17
    D03D    2010237  2286324   47.534700 -123.089400    0.2620 Eldon, WA, USA                                     ss   D03D      0.0000    0.0000 2011-10-11 13:07:17
    F04D    2009318  2286324   46.082900 -123.010800    0.2360 Rainier, OR, USA                                   ss   F04D      0.0000    0.0000 2011-10-11 13:07:17


Read a flat file Site table into a database

    from pisces.schema.css3 import Base

    session = sa.orm.Session(engine)
    Site, = ps.get_tables(session.bind, ['TA_site'], base=Base)
    
    with open('TA.site') as ffsite:
        for line in ffsite:
            isite = Site.from_string(line)
            session.add(isite)
    session.commit()


## Export

Next, we'll write database results to a flat file.  These work because the `info` dictionary in the underlying columns tell the class what the string version of itself should look like.

Here, we write 30 origins to a flat file.

    with open('TA.origin', 'w') as fforigin:
        for iorigin in session.query(Origin).filter(Origin.auth == 'REB-IDC').limit(30):
            fforigin.write(str(iorigin) + os.linesep)

#### TA.origin

      -6.121700  130.688500    0.0000   954927209.28000    620218    316285  2000096   60   40   -1      280       24 qp      -999.0000 g    5.60    299796    4.30    299797    6.10    299795 man:inversion   REB-IDC                     -1 2002-06-11 00:00:00
      -4.824500  102.976700   47.7000   954988491.91000    620219    316334  2000097   20   17   -1      274       24 qp      -999.0000 f    4.10    299798    3.20    299799 -999.00        -1 man:inversion   REB-IDC                     -1 2002-06-11 00:00:00
      39.195900   24.608700    0.0000   954974602.21000    620220    316319  2000096   16   15   -1      365       30 qp      -999.0000 g    3.80    299801    3.20    299802    3.80    299800 man:inversion   REB-IDC                     -1 2002-06-11 00:00:00
      22.291000  143.776500  115.8000   954732444.39000    620221    316167  2000094   15   13   -1      213       18 qp      -999.0000 f    3.50    299803 -999.00        -1 -999.00        -1 man:inversion   REB-IDC                     -1 2002-06-11 00:00:00
      -9.797000   66.893100    0.0000   954980391.62000    620222    316324  2000097   19   11   -1      429       33 qp      -999.0000 g    4.20    299804    4.10    299805 -999.00        -1 man:inversion   REB-IDC                     -1 2002-06-11 00:00:00


### Write flat files from any combination of columns

Ad-hoc collections of columns can be also written to well-formed flat files, with the right schema-specific format.
Queries on specific columns return a list of tuple-like objects called [KeyedTuples](http://docs.sqlalchemy.org/en/rel_0_9/orm/query.html#sqlalchemy.util.KeyedTuple), 
where values in individual records can be indexed into like a tuple, e.g. `record[0]`, 
or accessed via attributes, e.g. `record.lat, record.lon`. 

Let's write some network-station records to a text file.  First, get the string formatter for the columns you'll be using. 
`string_formatter` returns the correct format string from the [Python format specification mini-language](http://docs.python.org/2/library/string.html#format-specification-mini-language) for the columns you'll be writing. 
The columns must be known to `Base`.  That is, each column must have been defined in at least one table that inherited from `Base`.



    fmt = ps.string_formatter(Base.metadata, ['net', 'sta', 'lat', 'lon', 'elev'])
    print fmt
    
`fmt` looks like this:

    "{0:8.8s} {1:6.6s} {2:11.6f} {3:11.6f} {4:9.4f}"

Now, get the records and write them to file.

    q = session.query(Affiliation.net, Site.sta, Site.lat, Site.lon, Site.elev)
    q = q.filter(Site.sta == Affiliation.sta)
    q = q.filter(Affiliation.net.in_(['TA', 'UU']))
    
    import os
    with open('adhoc.txt', 'w') as f:
        for netsta in q:
            f.write(fmt.format(*netsta) + os.linesep)

#### adhoc.txt

    TA       Y53A     33.855400  -83.583600    0.2340
    TA       Y54A     33.862100  -82.688000    0.1760
    TA       Z38A     33.259900  -94.985100    0.1160
    TA       Z49A     33.194200  -86.531100    0.1340
    TA       Z50A     33.254000  -85.922600    0.3700
    TA       Z51A     33.316700  -85.174700    0.2490
    TA       Z52A     33.189300  -84.417600    0.2520
    TA       Z53A     33.280100  -83.571300    0.1440
    TA       Z54A     33.236200  -82.841700    0.1340
    TA       Z55A     33.221100  -82.135900    0.1000
    UU       EOCU     40.777000 -111.899100    1.3560
    UU       QJMH     40.703500 -111.866100    1.3120
    UU       QJOT     40.741600 -111.493900    1.9770
    UU       QKSL     40.377100 -111.861000    1.3790
    UU       QLIN     40.347200 -111.694700    1.5380
    UU       QMDS     40.729000 -111.816100    1.4050
    UU       QNRL     41.740700 -111.824900    1.4070
    UU       QPAY     40.053000 -111.728400    1.4040
    UU       QPML     40.057800 -111.953900    1.3340
    UU       QRJG     40.260900 -111.632700    1.5300
    ...


