from pisces import stations
from obspy.core import inventory

def build_inventory(session, stas, nets, chans, times, level)
    
    # how closely do we want to keep with obspy fdsn client get_stations 
    # no location, handle networks differently
    # reduce variablaes with ranges?
    # what is level default?  parse through obspy documentation for their default?
