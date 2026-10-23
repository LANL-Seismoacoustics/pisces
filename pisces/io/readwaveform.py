"""Deprecated compatibility module; use :mod:`pisces.io.waveforms` instead."""
import warnings

warnings.warn(
    "pisces.io.readwaveform is deprecated; import from pisces.io.waveforms "
    "instead. This compatibility module will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from pisces.io.waveforms import *
