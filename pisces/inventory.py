from pisces import stations
from obspy.core import inventory

def make_inventory(query, level='station', filename = None, format=None):

    # take query output from filtering functions and turn into an inventory object

    # check level and see if net is available

    Network, Affiliation, Site, Sitechan, Sensor, Instrument = _get_entities(query, "Network", "Affiliation","Site","Sitechan","Sensor","Instrument")