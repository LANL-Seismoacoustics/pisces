
def mseedhdr2tables(stats, wfdisc=None, site=None, sitechan=None, affiliation=None):
    """
    Scrapes an ObsPy Stats header instance into various database table rows.

    If table classes are provided, filled class instances are returned,
    otherwise dicts are returned.

    Parameters
    ----------
    stats : obspy.core.Stats instance
    wfdisc, site, sitechan : SQLAlchemy ORM table classes

    Returns
    -------
    rows : dict
        Keys are canonical table names, values are lists of dicts or class instances.
    
    Notes
    -----
    wfdisc.datatype is set to 'sd', which is not an actual KB Core or CSS 3.0
    datatype, but is supported within Pisces, and does not require data
    reformating/copying.

    """
    # 1. Assign stats values to column values
    # 2. Assign column values to table row dicts
    # 3. If provided, convert row dicts to class instances
    # 4. Return results as a dict of lists.

    # 1.
    net = stats['network']
    sta = stats['station']
    chan = stats['channel']
    samprate = stats['sampling_rate']
    nsamp = stats['npts']
    calib = stats.get('calib', 1.0)
    _time = stats['starttime'].timestamp
    _endtime = stats['endtime'].timestamp

    # 2.
    wfrow = {'sta': sta,
             'chan': chan,
             'time': _time,
             'endtime': _endtime,
             'calib': calib,
             'datatype': 'sd'}

    siterow = {'sta': sta}
    
    sitechanrow = {'sta': sta,
                   'chan': chan}
    
    # 3.
    if wfdisc:
        wfdiscrow = wfdisc(**wfdiscrow)
    
    if site:
        siterow = site(**siterow)
    
    if sitechan:
        sitechanrow = sitechan(**sitechanrow)

    # 4.
    rows = {'wfdisc': [wfdisc],
            'site': [site],
            'sitechan': [sitechan]}
    
    return rows
