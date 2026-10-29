from obspy.core.inventory import (
    Inventory, Network as ObsNetwork, Station, Channel,
    Site as ObsPySite, Equipment, Comment)
from obspy import UTCDateTime
from pisces.io.response import read_pazfir
import warnings
from collections import defaultdict
from pisces.util import _get_entities, jdate_to_utc

def schema_import(schema):
    schema = schema.lower()
    VALID_SCHEMAS = ['kbcore', 'css3', 'antelope']
    if schema not in VALID_SCHEMAS:
        raise ValueError(f"schema must be one of {VALID_SCHEMAS}")
    
    if schema == 'kbcore':
        from pisces.schema.kbcore import Network, Affiliation, Site, Sitechan, Sensor, Instrument

    if schema == 'css3':
        from pisces.schema.css3 import Network, Affiliation, Site, Sitechan, Sensor, Instrument
    
    if schema == 'antelope':
        from pisces.schema.css3 import Network, Affiliation, Site, Sitechan, Sensor, Instrument
    
    return Network, Affiliation, Site, Sitechan, Sensor, Instrument

def build_inventory(query, use_network = True, level = 'station', schema = 'kbcore'):

    # add in schema option with multiple import if statements...
    # schema = schema.lower()
    # VALID_SCHEMAS = ['kbcore', 'css3', 'antelope']
    # if schema not in VALID_SCHEMAS:
    #     raise ValueError(f"schema must be one of {VALID_SCHEMAS}")
    
    # if schema == 'kbcore':
    #     from pisces.schema.kbcore import Network, Affiliation, Site, Sitechan, Sensor, Instrument

    # if schema == 'css3':
    #     from pisces.schema.css3 import Network, Affiliation, Site, Sitechan, Sensor, Instrument
    
    # if schema == 'antelope':
    #     from pisces.schema.css3 import Network, Affiliation, Site, Sitechan, Sensor, Instrument

    Network, Affiliation, Site, Sitechan, Sensor, Instrument = schema_import(schema)

    level = level.lower()
    VALID_LEVELS = ['network', 'station', 'channel', 'response']
    if level not in VALID_LEVELS:
        raise ValueError(f"level must be one of {VALID_LEVELS}")
    
    # Get tables from query
    Network, Affiliation, Site, Sitechan, Sensor, Instrument = _get_entities(query, "Network", "Affiliation","Site","Sitechan","Sensor","Instrument")

    # Check tables are present for different level requests
    if level == 'network':
        if not Network:
            msg = "Network table required for station metadata"
            raise ValueError(msg)

    if level == 'station':
        if not Site:
            msg = "Site table required for station metadata"
            raise ValueError(msg)
        
    if level == 'channel':
        if not any([Site, Sitechan]):
            msg = "Site and Sitechan tables required for channel metadata"
            raise ValueError(msg)

    if level == 'response':
        if not any([Site, Sitechan, Sensor, Instrument]):
            msg = "Site, Sitechan, Sensor, and Instrument tables required for responses"
            raise ValueError(msg)
        
    # Execute query and organize results
    results = query.all()

    data_structure = organize_data(results, use_network=use_network,schema = schema)

    # Build inventory based on level
    networks = []
    for net_code, net_data in data_structure.items():
        network = build_network(net_code, net_data, level)
        if network is not None:
            networks.append(network)
    
    return Inventory(
        networks = networks,
        source = "KB Core Database via Pisces",
        created = UTCDateTime()
    )

def organize_data(results, use_network = True, schema = 'kbcore'):
    """
    Organize query results into nested dictionary structure.
    
    Returns: {network_code: {station_code: {channel_key: [data]}}}
    """
    Network, Affiliation, Site, Sitechan, Sensor, Instrument = schema_import(schema)

    data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    
    if not results:
        warnings.warn("Query returned no results")
        return Inventory(networks=[], source="KB Core via Pisces")    
    
    for row in results:
        site = extract_table(row, Site)
        sitechan = extract_table(row, Sitechan)
        sensor = extract_table(row, Sensor)
        instrument = extract_table(row, Instrument)
        affiliation = extract_table(row, Affiliation)
        network = extract_table(row, Network)

        if network and use_network == True:
            net_name = network.netname
            if net_name == '-' or net_name is None:
                net_name = 'Netname in Network table is Null'
            if Affiliation:
                net_code = affiliation.net
            else:
                net_code = network.net
        else:
            net_code = '__'
            net_name = 'Pisces Default Network Code if none are provided or available'
        
        # Store network metadata
        if 'metadata' not in data[net_code]:
            data[net_code]['metadata'] = {
                'network': network,
                'description': net_name
            }
        
        # Store station metadata
        if site:
            sta_key = (site.sta, site.ondate)
            if 'metadata' not in data[net_code][sta_key]:
                data[net_code][sta_key]['metadata'] = {
                    'site': site,
                    'affiliation': affiliation
            }
        
        # Store channel data
        if sitechan:
            # Use (chan, ondate, offdate) as unique key for each channel epoch
            chan_key = (sitechan.chan, sitechan.ondate, sitechan.offdate)
            data[net_code][sta_key][chan_key].append({
                'sitechan': sitechan,
                'sensor': sensor,
                'instrument': instrument
            })
    
    return data


def extract_table(row, table_class):
    """Extract specific table object from query row."""
    # Try multiple methods to get the table
    # Method 1: Direct attribute access
    if hasattr(row, table_class.__name__.lower()):
        return getattr(row, table_class.__name__.lower())
    
    # Method 2: Check if row is tuple-like
    if isinstance(row, tuple):
        for item in row:
            if isinstance(item, table_class):
                return item
    
    # Method 3: Check if row is the table itself
    if isinstance(row, table_class):
        return row
    
    return None



def build_network(net_code, net_data, level):
    """Build ObsPy Network object."""
    metadata = net_data.get('metadata', {})
    network_obj = metadata.get('network')
    
    # For 'network' level, return basic network info only
    if level == 'network':
        return ObsNetwork(
            code = net_code,
            description = metadata.get('description', f"Network {net_code}"),
        )
    
    # Build stations for other levels
    stations = []
    for sta_code, sta_data in net_data.items():
        if sta_code == 'metadata':
            continue
        station = build_station(sta_code, sta_data, level)
        if station is not None:
            stations.append(station)

    if not stations:
        return None
    
    return ObsNetwork(
        code = net_code,
        description = metadata.get('description', f"Network {net_code}"),
        stations = stations,
    )


def build_station(sta_key, sta_data, level):
    """Build ObsPy Station object."""
    metadata = sta_data.get('metadata', {})
    site = metadata.get('site')
    
    if not site:
        return None
    
    sta_code = sta_key[0]

    if site.ondate == -1:
        start_time = None
    else:
        start_time = jdate_to_utc(site.ondate)

    if site.offdate == 2286324:
        end_time = None
    else:
        end_time = jdate_to_utc(site.offdate)
    
    if site.staname == '-':
        sta_name = 'Staname in Site table is Null'
    else:
        sta_name = site.staname

    station = Station(
        code = sta_code,
        latitude = site.lat,
        longitude = site.lon,
        elevation = site.elev*1000,
        site = ObsPySite(name=  sta_name or sta_code),
        start_date = start_time,
        end_date = end_time,
    )
    
    # Add reference station if available
    if hasattr(site, 'refsta') and site.refsta:
        station.comments.append(Comment(value=f"Reference station: {site.refsta}"))
    
    # For 'station' level, return without channels
    if level == 'station':
        return station
    
    # Build channels for 'channel' and 'response' levels
    channels = []
    for chan_key, chan_data_list in sta_data.items():
        if chan_key == 'metadata':
            continue
        for chan_data in chan_data_list:
            try:
                channel = build_channel(
                    site = site,
                    chan_data = chan_data,
                    include_response = (level == 'response')
                )
                if channel is not None:
                    channels.append(channel)
            except Exception as e:
                warnings.warn(f"Error building channel {chan_key[0]} for {sta_code}: {e}")
    
    station.channels = channels
    return station


def build_channel(site, chan_data, include_response=False):
    """Build ObsPy Channel object."""
    sitechan = chan_data['sitechan']
    sensor = chan_data['sensor']
    instrument = chan_data['instrument']

    
    # Location code
    location_code = ''

    if sitechan.ondate == -1:
        start_time = None
    else:
        start_time = jdate_to_utc(sitechan.ondate)

    if sitechan.offdate == 2286324:
        end_time = None
    else:
        end_time = jdate_to_utc(sitechan.offdate)

    if sitechan.descrip == '-':
        chan_descrip = 'Descrip in Sitechan table is Null'
    else:
        chan_descrip = sitechan.descrip

    
    # Calculate dip from vang
    # KB Core: vang=0 horizontal, vang=90 up, vang=-90 down
    # SEED: dip=0 horizontal, dip=90 down, dip=-90 up
    if sitechan.vang == -1 or sitechan.vang is None:
        dip = None
    else:
        dip = 90.0 - sitechan.vang

    if sitechan.hang == -1 or sitechan.hang is None:
        azimuth = None
    else:
        azimuth = sitechan.hang
    
    # Sample rate from instrument
    if instrument:
        sample_rate = float(instrument.samprate)
    else:
        sample_rate = None

    channel = Channel(
        code = sitechan.chan,
        location_code = location_code,
        latitude = site.lat,
        longitude = site.lon,
        elevation = site.elev*1000,
        depth = sitechan.edepth*1000,
        azimuth = azimuth,
        dip = dip,
        sample_rate = sample_rate,
        start_date = start_time,
        end_date = end_time,
        description = chan_descrip
    )

    # Add sensor equipment
    if instrument:
        channel.sensor = Equipment(
            type = instrument.insname,
            description = getattr(instrument, 'instype', instrument.insname) if instrument else instrument.insname
        )
    
    # Add chanid comment
    channel.comments.append(Comment(value=f"Channel ID: {sitechan.chanid}"))
    
    # Build response if requested

    # Add schema specific calls here since Antelope can support VEL and ACC
    if include_response and sensor and instrument:
        if instrument.rsptype == 'A':
            resp_units = 'ACC'
        elif instrument.rsptype == 'V':
            resp_units = 'VEL'
        elif instrument.rsptype == 'D':
            resp_units = 'DISP'
        elif instrument.rsptype == 'I':
            resp_units = 'PRESSURE'
        else:
            if sitechan.chan[1].upper() == 'D':
                resp_units = 'PRESSURE'
            elif sitechan.chan[1].upper() in ['H', 'L', 'N', 'G', 'M', 'P']:
                resp_units = 'DISP'
            else:
                VALID_CODES = ['H', 'L', 'N', 'G', 'M', 'P', 'D']
                msg = f"Instrument response reader expecting channel codes with instrument codes in {VALID_CODES} "
                raise ValueError(msg)
                   
        response = build_response(sensor, instrument, sample_rate, resp_units)
        if response:
            channel.response = response
    
    return channel

def build_response(sensor, instrument, sample_rate, input_units):
    """Build ObsPy Response object from sensor calibration data."""
    response_path = f"{instrument.dir}/{instrument.dfile}"

    response= read_pazfir(response_path, sample_rate, instrument.ncalib, instrument.ncalper, input_units, calratio = sensor.calratio)

    return response

