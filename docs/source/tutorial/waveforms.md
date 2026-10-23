# Working with Waveforms

How to read and write waveforms.

## Retrieving waves from a query

Waveforms are described in the `Wfdisc` table, and there are two ways to get waveforms from a query.

### Read directly from `wfdisc` instances

If you have instances from the `Wfdisc` class, you can easily convert them to ObsPy `Trace`
instances for analysis or plotting.  Pisces Wfdisc class instances have a `to_trace` method,
which produces `Trace` instance from the `Wfdisc` instance.  Alternately, you can use the 
`wfdisc2trace` function on a vanilla SQLAlchemy Wfdisc instance (no `to_trace` method).
Finally, you can use the low-level function `read_waveform`, which underlies all the methods above.
This function returns a raw NumPy array instead of an Obspy Trace, however.

```python
from mytables import Wfdisc
from pisces import wfdisc2trace, read_waveform


# loop over 10 BHZ wfdisc instances from the database
for wf in session.query(Wfdisc).filter(Wfdisc.chan == 'BHZ').limit(10):
    # the following two traces should be the same
    tr = wf.to_trace()
    tr = wfdisc2trace(wf) 

    # get the raw data
    data = read_waveform(wf.dir + '/' + wf.dfile, wf.datatype, wf.foff, wf.nsamp)

    #do analysis, writing, and/or plotting here...

```

### Using the `pisces.Client` class

<!--

The `Client` class is instantiated to point to a database, and relevant table names can be targeted
using the `load_tables` method.  Thereafter, the table classes are available in the instance's
`.tables` dictionary attribute.  In the following example, we retrieve windowed waveforms 
around predicted P and surface wave arrivals for some large events in 2010.

```python
import pisces as ps
from pisces.client import Client

client = Client('sqlite:///mydb.sqlite')

tables = {'site': 'TA_site',
          'sitechan': 'TA_sitechan',
          'origin': 'TA_origin',
          'wfdisc': 'TA_wfdisc'}
client.load_tables(**tables)

# collect events with mb > 5.4 in 2010
# database times are epoch times, so we convert them from YYYYJJJ using ObsPy's `UTCDateTime` class
t0 = UTCDateTime('2010001').timestamp
t1 = UTCDateTime('2010365').timestamp
events = client.get_events(time=(t0, t1), deg=(40, -105, 30, 90), mag={'mb': (5.4, 10)})

# collect BHZ channels in the western US
stations = client.get_stations(channels=['BHZ'], region=(-110, -100, 35, 45))

for i, ievent in enumerate(events):
    for istation in stations:
        # predict a window between first P and 2.5 km/s (surface wave) arrival times
        deg = geod.locations2degrees(ista.lat, ista.lon, ievent.lat, ievent.lon)
        ttp, tts = ps.travel_times(['P', 2.5], deg=deg, depth=ievent.depth)
        st = client.get_waveforms(ista.sta, 'BHZ', i.time+ttp-60, i.time+tts+60)
        # write each trace as a SAC file
        for ii, wf in enumerate(st):
            # write to disk like "0_TA.M14A..BHZ_0.SAC" 
            tr.write("{}_{}_{}.SAC".format(i, tr.id, ii), format='SAC')
```
First, the client is instantiated with a database connection URL.
Next, the required station, event, and data tables are loaded with `load_tables`.
The `get_events` method is called to request events in 2010 with mb >= 5.4 that
are 30-90 epicentral degrees from latitude 40, longitude -105, returning a list
of Origin class instances (table rows). As the distance calculation is done
out-of-database, all events that match the other criteria are loaded first
before applying the distance filter. For large result sets, this can be
memory-intensive without an additional in-database filter, such as a region box
or smaller magnitude range. The `get_stations` method collects BHZ channels in
the western US, and returns a list of Site instances. Finally, we loop through
events and stations to predict a travel time window at each station using `travel_times` function, 
request the corresponding waveforms (as a collection of ObsPy Trace objects, called a `Stream`) 
using `get_waveform`, and write each trace to disc as a SAC file using the ObsPy Trace object write
method, which supports several output formats, including miniSEED.

-->

---


## Adding waveform files to a database

Pisces can use SAC and miniSEED files as the waveform files behind a CSS 3.0
or KB Core-style database. Importing records each file's location and the
metadata available in its header; it does not copy or convert the waveform
samples.

### Choose a format

**SAC** files can contribute waveform, station, channel, network, instrument,
event, origin, arrival, and association metadata when those headers are
present. This makes SAC useful when a file includes both waveform and event
context.

**miniSEED** files provide waveform data and basic network, station, and
channel identity. They generally do not contain enough information to make a
complete station or channel record.

### Review imported metadata

A file header is not a complete database. Before relying on imported records,
review and fill in metadata that the format cannot provide, such as:

- station and channel effective dates and station coordinates;
- database identifiers and links between related event records;
- the file location recorded with each waveform, particularly when data is
  moved to another system.

SAC header fields are conventions maintained by the data producer. For example,
event details and phase picks are available only when they were written to the
file. Treat file import as a starting point for database metadata, then
validate it against the authoritative deployment and event information.

Once waveform records point at accessible files, retrieve them as ObsPy
`Trace` objects through the `Wfdisc` workflow above. Pisces uses the database
record for the returned trace's identifying and timing metadata, so corrections
made in the database are reflected when the waveform is read.

For Python import details and the exact fields available from each format, see
the API reference for `pisces.io.sac` and `pisces.io.mseed`.

---


## Copying (localizing) waveform files

If you want to move waveform files from one database to another one, you may need copy the files
and tweak the Wfdisc table.  Wfdisc tables contain
file name and directory information about the waveforms stored on disk, so those need to be 
corrected when you move the files.  In the example below, we copy wfdisc instances from `session1`,
pointing to the originating database, to `session2`, which points at the destination database.

```python
import os
import shutil

def copy_waves(wfdiscs, old_base, new_base):
    """Replace old_base with new_base in the .dir attribute of wfdisc list, and copies the 
    waveform files to the new location.

    Parameters
    ----------
    wfdiscs : list
        Wfdisc instances from source database.
    old_base, new_base : str
        The top of the old (new) data directory trees.  This assumes all wfdiscs originate and 
        end up under single directories. The directory structure under the new_base will mirror
        that under old_base.

    Returns
    -------
    wfdiscs_out : list
        Same as input list, but .dir attribute now points to the new_base location.  

    """
    for wf in wfdiscs:
        # replace the directory
        old_file =  os.path.sep.join([wf.dir, wf.dfile])
        wf.dir.replace(old_base, new_base)
        new_file =  os.path.sep.join([wf.dir, wf.dfile])
        try:
            shutil.copyfile(old_file, new_file)
        except IOError:
            # new directory doesn't exist yet.  this is like "mkdir -p" 
            os.makedirs(os.path.dirname(new_file))
            shutil.copyfile(old_file, new_file)

# get the wfdiscs
wfs = session1.query(Wfdisc1).all()

# release the link between the wfdiscs and the originating database
# this makes them "floating" instances, so they can be added to the destination database
session1.expunge_all(wfs)

# do the copy and tweaking
wfs = copy_waves(wfs, '/old/path/to/top/of/data', '/my/new/path/to/top/of/data')

# add and commit them to the destination database
session2.add_all(wfdiscs)
session2.commit()

```
