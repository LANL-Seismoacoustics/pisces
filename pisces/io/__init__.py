"""
pisces.io: read KB Core-pointed waveform/response files, convert their
headers to/from table rows.

Reads the files a `wfdisc` or `instrument` row points to via
`dir`/`dfile`/`datatype`/`rsptype`. No database session or ORM awareness --
that's `pisces.trace`/`pisces.catalog`/`pisces.inventory`'s job.

`read_waveform(path, datatype, byteoffset, nsamp) -> ndarray` dispatches by
`wfdisc.datatype` string, via the `WAVEFORM_READERS` registry. New
datatypes can be registered from user code without editing pisces::

    from pisces.io.waveforms import WAVEFORM_READERS

    @WAVEFORM_READERS('myc')
    def read_myc(path, byteoffset=0, nsamp=None):
        ...
        return data

    from pisces.io import read_waveform
    data = read_waveform(path, 'myc', byteoffset, nsamp)

Per-format header<->table-row conversion lives one module per format
(`pisces.io.sac`, `pisces.io.mseed`), each exposing `trace2tables`.

"""
from pisces.io.waveforms import read_waveform, WAVEFORM_READERS
