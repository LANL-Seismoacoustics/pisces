from pisces import stations
from obspy.core import inventory as inv
from obspy.core import UTCDateTime

def make_inventory(query, level='station', filename = None, format=None):

    # take query output from filtering functions and turn into an inventory object

    # check level and see if net is available

    # Create mapping dictionaries where net is keywork and sta in corresponding list, do for primary keys down to response?

    # Get tables from query
    Network, Affiliation, Site, Sitechan, Sensor, Instrument = _get_entities(query, "Network", "Affiliation","Site","Sitechan","Sensor","Instrument")

    # Check tables are present for different level requests
    if level == 'station':
        if not any [Site]:
            msg = "Site table required for station metadata"
            raise ValueError(msg)
        
    if level == 'channel':
        if not any [Site, Sitechan, Sensor, Instrument]:
            msg = "Site, Sitechan, Sensor, and Instrument tables required for channel metadata"
            raise ValueError(msg)

    if level == 'response':
        if not any [Site, Sitechan, Sensor, Instrument]:
            msg = "SSite, Sitechan, Sensor, and Instrument tables required for responses"
            raise ValueError(msg)
        
    inventory = Inventory(
            networks=[])
    
    #if Network:
        

    # if level == 'network':

    netStaDict = {}
    netObjDict = {}
    staChanDict = {}
    staObjDict = {}
    chanRespDict = {}
    chanObjDict = {}
    respObjDict = {}

    for row in query:
        # start with network, get network value if exists if not exist then '__'
        if Network:
            netcode = row.network.net
            netname = row.network.netname
            auth = row.network.auth
        else:
            netcode = '__'
            netname = 'Default network when none provided in query'
            auth = 'Pisces Default'
        
        # create Network object if not already created
        netObj = inv.Network(netcode, description = netname, source_id=auth)  # return later and count netStaDict entries and add to total number of stations, add staObj list to stations field
        
        if Affiliation:
            netStart = UTCDateTime(row.affiliation.time)
            netEnd = UTCDateTime(row.affiliation.endtime)

            if netStart.timestamp != -9999999999.999:
                netObj.start_date = netStart
            if netEnd.timestamp != 9999999999.999:
                netObj.end_date = netEnd

            if netcode in netStaDict:  # check if network in netStaDict as key, if not add as key with station in list, if so add sta
                netStaDict[netcode].append(row.affiliation.sta)
            else:
                netStaDict[netcode] = [row.affiliation.sta]

        
        if netcode not in netObjDict:
                    netObjDict[netcode] = netObj
        

        # Next move to station tables

        if Site:
            stacode = row.site.sta
            staname = row.site.staname
            latitude = row.site.latitude
            longitude = row.site.longitude
            elevation = row.site.longitude*1000

            staObj = inv.Station(stacode, latitude, longitude, elevation, site = staname)
        else:  
            continue

        

        