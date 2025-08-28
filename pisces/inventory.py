from pisces import stations
import obspy.core import inventory as inv
from obspy.core import UTCDateTime
import datetime
from pisces.io.response import read_pazfir

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
        
    inventory = inv.Inventory(
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
            netObj = inv.Network(netcode)  #TODO:  return later and count netStaDict entries and add to total number of stations, add staObj list to stations field
            if row.network.netname != '-':
                netObj.description = row.network.netname
            if row.network.auth != '-':
                netObj.source_id = row.network.auth
        else:
            netcode = '__'
            netname = 'Default network when none provided in query'
            auth = 'Pisces Default'
            netObj = inv.Network(netcode, description = netname, source_id=auth)
        
        if Affiliation:
            if not Network:
                netcode = row.affiliation.net
                netObj = inv.Network(netcode)

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

        if level != 'network':
            # Will always need site/station unless level is network
            stacode = row.site.sta
            staObj = inv.Station(stacode)
            if row.site.staname != '-':
                staObj.description = row.site.staname
            if row.site.lat != -999:            #TODO: required for channel object, what to do?
                staObj.latitude = row.site.lat
            if row.site.lon != -999:
                staObj.longitude = row.site.lon
            if row.site.elev != '-999':
                staObj.elevation = row.site.elev*1000
            if row.site.ondate != -1:
                staObj.start_date = UTCDateTime(datetime.datetime.strptime(row.site.ondate, '%Y%j').date())
            if row.site.offdate != 2286324:
                staObj.end_date = UTCDateTime(datetime.datetime.strptime(row.site.offdate, '%Y%j').date())
            
            #TODO: if stacode not in staObjDict
            
            if Sitechan:
                chancode = row.sitechan.chan
                chanid = row.sitechan.chanid
                location_code = ''
                chanObj = inv.Channel(chancode, location_code, row.site.lat, row.site.lon, row.site.lon, \
                                      row.site.elev*1000, row.sitechan.edpeth)
                if row.sitechan.hang != -1:
                    chanObj.azimuth = row.sitechan.hang
                if row.sitechan.vang != -1:
                    chanObj.dip = row.sitechan.vang
                if row.sitechan.descrip != '-':
                    chanObj.description = row.sitechan.descrip
                if row.sitechan.ctype != '-':
                    chanObj.types = row.sitechan.ctype
                if row.sitechan.ondate != -1:
                    chanObj.start_date = UTCDateTime(datetime.datetime.strptime(row.sitechan.ondate, '%Y%j').date())
                if row.sitechan.offdate != 2286324:
                    chanObj.end_date = UTCDateTime(datetime.datetime.strptime(row.sitechan.offdate, '%Y%j').date())
            
            if Sensor:
                if row.sensor.time != -9999999999.999:
    
        #### THE SAME CHANID CAN MAP TO MULTIPLE INIDS, WILL NEED TO ACCOUNT HERE AND ALSO IN STATIONS.PY

        ## NOTE TO SELF:  START MAPPING LOGIC AT BOTTOM AND WORK UP 
    

            if Instrument:
                chanObj.sample_rate = row.instrument.samprate

            if level == 'response':
                calib = row.instrument.ncalib
                calper = row.instrument.ncalper
                calratio = row.sensor.calratio

                if row.instrment.dir != '-' and row.instrument.dfile !=  '-':
                    filepath = '{}/{}'.format(row.instrment.dir,row.instrment.dfile)
                    chanObj.response = read_pazfir(filepath, cailb = calib, calper = calper, input_units='M', calratio = calratio)
                else:
                    chanObj.response = None ### DOES THIS MAKE SENSE?





        else:  
            pass # TODO: check if pass or continue...

    
    return inventory
        

        