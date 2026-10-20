# Converted to python 3.5.2 on 02/07/17
# By: Jeremy Webster

"""
Raw waveform sample-vector reading, dispatched by ``wfdisc.datatype``.

Plain NumPy-compatible binary layouts (``NPTYPE`` below) are read generically
by `read_numpy`, keyed only by their NumPy dtype string -- no registration
needed. Everything else (data requiring a real decoder: miniSEED, SEGY,
compressed formats, etc.) is read by a function registered in
`WAVEFORM_READERS`, keyed by its `wfdisc.datatype` string.

`WAVEFORM_READERS` is a plain `pisces.io.util.Registry`, so new datatypes can
be added from user code without editing pisces, e.g.::

    from pisces.io.readwaveform import WAVEFORM_READERS

    @WAVEFORM_READERS('my_dtype')
    def read_my_dtype(path, byteoffset=0, nsamp=None):
        ...

Note that ``'sd'`` (miniSEED/SEED) and ``'sc'`` (SAC), as well as the numeric
NumPy types, are not official KB Core `wfdisc.datatype` values -- they're
pisces conveniences, and the files they point to may hold header metadata
that's stale relative to the database tables. ``'sc'`` in particular is
mostly redundant with the plain float NumPy types (SAC's own on-disk sample
array *is* just a big/little-endian ``f4`` vector at a known byte offset);
it's kept here only as a convenience for reading a standalone SAC file
wholesale through ObsPy, ignoring `byteoffset`/`nsamp`.

"""
import os
from io import BytesIO

import numpy as np
from obspy.core import read

from pisces.io.util import Registry

try:
    import e1
    E1_INSTALLED = True
except ImportError:
    E1_INSTALLED = False

# registry of functions: (path, byteoffset, nsamp) -> ndarray, keyed by
# wfdisc.datatype string.
WAVEFORM_READERS = Registry()

# NumPy-supported datatypes {datatype: numpy.dtype}, read generically by
# read_numpy() below; not individually registered.
NPTYPE = {
    't4': '>f4',
    't8': '>f8',
    's4': '>i4',
    's2': '>i2',
    's1': '>i1',
    'f8': '<f8',
    'f4': '<f4',
    'i4': '<i4',
    'i2': '<i2',
    'i1': '<i1',
    'p8': '<f8',
    'p4': '<f4',
    'u4': '<f4',
}


def read_waveform(DATAFILE, DATATYPE, BYTEOFFSET, NUM):
    """
    Read a data vector of a certain data type.

    Parameters
    ----------
    DATAFILE : string
        Path and name of data file.
    DATATYPE : string
        {'f4', 'i1', 'i2', 'i4', 'p4', 't8', 's2', 'p8', 's4', 'f8', 'u4', 't4',
         's1', 'sd', 'e1', 'sc', 'sy', 's3', ...}
        Data type string (from wfdisc.datatype).
        'sd', 'sc', and 'sy' are SEED/miniSEED, SAC, and SEGY (pisces
        conveniences, not official KB Core values -- see module docstring).
        'e1' requires installation of the "e1" python module.
        Additional datatypes can be registered via `WAVEFORM_READERS`.
    BYTEOFFSET : int
        Number of bytes from beginning of file.
    NUM : int
        Number of samples to read.

    Returns
    -------
    data : numpy.array
        Vector of NUM samples of type DATATYPE.

    Raises
    ------
    ValueError
        Unrecognized DATATYPE.
    IOError
        DATAFILE does not exist.

    Notes
    -----
    If the file has a header and you want it, you'll have to read it manually
    with obspy.core.read or something else.

    """
    if DATATYPE in NPTYPE:
        return read_numpy(DATAFILE, BYTEOFFSET, NUM, 'rb', NPTYPE[DATATYPE])

    try:
        reader = WAVEFORM_READERS[DATATYPE]
    except KeyError:
        raise ValueError("Unrecognized data format: {0}".format(DATATYPE))

    return reader(DATAFILE, BYTEOFFSET, NUM)


@WAVEFORM_READERS('sd')
def read_seed(DATAFILE, BYTEOFFSET=0, NUM=None):
    """Read a SEED or miniSEED 'sd' datatype.
    """
    if BYTEOFFSET:
        with open(DATAFILE, 'rb') as f0:
            f0.seek(BYTEOFFSET)
            # unfortunately, this read command reads every header
            tr = read(f0, format='MSEED', details=True, headonly=True)[0]
            f0.seek(BYTEOFFSET)
            nbytes = tr.stats.mseed.number_of_records * tr.stats.mseed.record_length
            f = BytesIO(f0.read(nbytes))

        tr = read(f, format='MSEED')[0]
    else:
        tr = read(DATAFILE, format='MSEED')[0]

    if NUM:
        assert len(tr.data) == NUM

    return tr.data


@WAVEFORM_READERS('sc')
def read_sac(DATAFILE, BYTEOFFSET=0, NUM=None):
    """
    Read a standalone SAC file's data through ObsPy, ignoring BYTEOFFSET/NUM.

    See the module docstring -- 'sc' is a pisces convenience, redundant with
    the plain float NumPy datatypes for most purposes.

    """
    return read(DATAFILE, format='SAC')[0].data


@WAVEFORM_READERS('sy')
def read_segy(DATAFILE, BYTEOFFSET=0, NUM=None):
    """Read a standalone SEGY file's data through ObsPy."""
    return read(DATAFILE, format='SEGY')[0].data


@WAVEFORM_READERS('e1')
def read_e1(DATAFILE, BYTEOFFSET, NUM):
    """Read an 'e1'-compressed datatype. Requires the 'e1' package."""
    if not E1_INSTALLED:
        msg = "'e1' module not installed.  Visit https://github.com/LANL-Seismoacoustics/e1 for details."
        raise ValueError(msg)
    with open(DATAFILE, 'rb') as f:
        f.seek(BYTEOFFSET)
        return e1.decompress_file(f, NUM)


@WAVEFORM_READERS('s3')
def read_s3(DATAFILE, BYTEOFFSET, NUM):
    """
    Read signed big-endian 3-byte integers into a 4-byte native NumPy array.

    """
    try:
        with open(DATAFILE, 'rb') as f:
            f.seek(BYTEOFFSET, 0)
            u1 = np.fromfile(f, dtype='u1', count=NUM*3)
    except TypeError:
        f = DATAFILE
        f.seek(BYTEOFFSET, 0)
        u1 = np.fromfile(f, dtype='u1', count=NUM*3)

    prep = np.empty((NUM, 4), dtype='u1')
    # for little-endian output, put the empty byte on the left, and fill the
    # right 3 bytes with the raw data, with column order reversed.
    prep[:, 1:] = np.flip(u1.reshape((-1, 3)), axis=1)
    # now, reinterpret and copy the shifted n x 4 as 4-byte signed integers
    i4_unshifted = prep.view('i4')

    # now, bit-shift right, which sign-extends the 3 bytes to 4.
    # the empty left byte is re-written correctly by the shift.
    i4_shifted = i4_unshifted >> 8

    return i4_shifted.squeeze()


def read_numpy(DATAFILE, BYTEOFFSET, NUM, PERMISSION, DTYPE):
    """
    Read NumPy-compatible binary data.

    Modeled after MatSeis function read_file in util/waveread.m.

    """
    with open(DATAFILE, PERMISSION) as f:
        f.seek(BYTEOFFSET, 0)
        data = np.fromfile(f, dtype=np.dtype(DTYPE), count=NUM)

    return data
