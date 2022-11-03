# Converted to python 3.5.2 on 02/07/17
# By: Jeremy Webster

"""
Home to read_waveform and all format-specific reading functions.

"""
import ctypes as C
import os
from io import BytesIO

import numpy as np
from obspy.core import read

try:
    from e1 import e_compression
    E1_INSTALLED = True
except ImportError:
    E1_INSTALLED = False

# TODO: implement other datatypes

# NumPy-supported datatypes {datatype: numpy.dtype}
NPTYPE = {'t4': '>f4', 't8': '>f8', 's4': '>i4', 's2': '>i2', 's1': '>i1',
          'f8': '<f8', 'f4': '<f4', 'i4': '<i4', 'i2': '<i2', 'i1': '<i1',
          'p8': '<f8', 'p4': '<f4', 't4': '>f4', 'u4': '<f4'}

# ObsPy-supported datatypes
OBSPYTYPE = {'sc': 'SAC', 'sy': 'SEGY'}
# NOTE: 'sd' can also mean full SEED.


def read_waveform(DATAFILE, DATATYPE, BYTEOFFSET, NUM):
    """
    Read a data vector of a certain data type.

    Parameters
    ----------
    DATAFILE : string
        Path and name of data file.
    DATATYPE : string
        {'f4', 'i1', 'i2', 'i4', 'p4', 't8', 's2', 'p8', 's4', 'f8', 'u4', 't4',
         's1', 'sd', 'e1', 'sc', 'sy'}
        Data type string (from wfdisc.datatype).
        'sd', 'sc', and 'sy' are SEED/miniSEED, SAC, and SEGY
        'e1' requires installation of the "e1" python module.
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
    # TODO: do something with return flags
    if DATATYPE in NPTYPE:
        data = numpy_read(DATAFILE, BYTEOFFSET, NUM, 'rb', NPTYPE[DATATYPE])
    elif DATATYPE in OBSPYTYPE:
        data = read(DATAFILE, format=OBSPYTYPE[DATATYPE])[0].data
    elif DATATYPE == 'sd':
        # this datatype is not well-suited for a wfdisc, as it supports
        # multiplexing and wfdisc does not
        data = read_seed(DATAFILE, BYTEOFFSET, NUM)
    elif DATATYPE == 'e1':
        # data = read_e1(DATAFILE, BYTEOFFSET, NUM)
        if not E1_INSTALLED:
            msg = "'e1' module not installed.  Visit https://github.com/LANL-Seismoacoustics/e1 for details."
            raise ValueError(msg)
        else:
            data = e_compression(DATAFILE, BYTEOFFSET, NUM)
    elif DATATYPE == 's3':
        data = read_s3(DATAFILE, BYTEOFFSET, NUM)
    else:
        raise ValueError("Unrecognized data format: {0}".format(DATATYPE))

    # if len(data) not NUM:
    #    # TODO: raise something here
    #    pass

    return data


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



def numpy_read(DATAFILE, BYTEOFFSET, NUM, PERMISSION, DTYPE):
    """
    Read NumPy-compatible binary data.

    Modeled after MatSeis function read_file in util/waveread.m.

    """
    f = open(DATAFILE, PERMISSION)
    f.seek(BYTEOFFSET, 0)
    data = np.fromfile(f, dtype=np.dtype(DTYPE), count=NUM)
    f.close()

    return data
