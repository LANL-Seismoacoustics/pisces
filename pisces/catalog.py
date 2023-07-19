"""
from pisces.catalog import ETree

tree = ETree(query1, query2, resource_prefix='smi:lanl.gov')
tree.update(query3)
tree.catalog()

"""
import os

from obspy import UTCDateTime
import obspy.core.event as qml
from sqlalchemy import inspect

import pisces as ps
from pisces.util import _get_entities, dtree

# Convert KB Core etypes to FDSN event types, best good-faith mapping
# These are also used for a backwards mapping below, so where there multiple backwards mappings,
# the final one is preferred/used. Relies on order-preserving dictionaries in Python 3.7+.
FDSN_EVENT_TYPE = {
    "ec": 'chemical explosion', #chemical explosion",
    "ep": 'explosion', #probable explosion",
    "ex": 'explosion', #generic explosion",
    "en": 'nuclear explosion', #nuclear explosion",
    "mc": 'collapse', #collapse",
    "me": 'mining explosion', #coal bump/mining event",
    "mp": 'mining explosion', #probable mining event",
    "mb": 'rock burst', #rock burst",
    "qd": 'earthquake', #damaging earthquake",
    "qp": 'earthquake', #unknown-probable earthquake",
    "qf": 'earthquake', #felt earthquake",
    "qt": 'earthquake', #generic earthquake/tectonic",
    "ge": 'other event', #geyser",
    "xm": 'meteorite', #meteroritic origin",
    "xl": 'other event', #ligts",
    "xo": 'other event', #odors",
    '-': 'not reported',
    None: 'not reported',
}
# Convert FDSN event types to KB Core etypes, best good-faith mapping
# An FDSN event type without any corresponding etype doesn't appear here, and produces a None etype
KBCORE_EVENT_TYPE = {
    'accidental explosion': 'ec,ep,ex',
    'anthropogenic event': 'ec,ep,ex,en,mc,me,mp,mb',
    'atmospheric event': 'xm,xl,xo',
    'blasting levee': 'ec,ep,ex',
    'cavity collapse': 'mc',
    'chemical explosion': 'ec',
    'collapse': 'mc,mb',
    'controlled explosion': 'ec,ep,ex,en',
    'earthquake': 'qd,qp,qf,qt',
    'experimental explosion': 'ec,ep,ex',
    'explosion': 'ec,ep,ex',
    'ice quake': 'qp,qt',
    'industrial explosion': 'ec,ep,ex',
    'meteorite': 'xm',
    'mine collapse': 'mc,mb',
    'mining explosion': 'me,mp',
    'not existing': '-',
    'not reported': '-',
    'nuclear explosion': 'en',
    'other event': '-',
    'quarry blast': 'ec,ex,me,mp',
    'rock burst': 'mb',
    'sonic blast': 'xl,xo',
    'sonic boom': 'xl,xo',
    'thunder': 'xl,xo',
}

# arrival.qual
FDSN_PICK_ONSET = {
    'i': 'impulsive',
    'e': 'emergent',
    'w': 'questionable', # weak
    '-': None,
}

# arrival.fm
FDSN_POLARITY = {
    'c': 'positive',
    'u': 'positive',
    'd': 'negative',
    'r': 'negative',
    '-': 'undecidable',
}


class ETree:
    """
    Event tree

    Turn redundant tabular data from a database into nonredudant hierarchical data
    roughly mirroring the structure of QuakeML/obspy.Catalog.

    Parameters
    ----------
    event_queries : one or more sqlalchemy.orm.Query instances
        one or more result sets from events.filter_* functions, like
        (column order is not important):

        event1, origin1
        event1, origin2
        event2, origin3
        event2, origin4
        ...
        or
        event1, origin1, netmag1
        event1, origin1, netmag2
        event1, origin1, netmag4
        event1, origin2, netmag5
        event2, origin3, netmag6
        ...
        or
        event1, origin1, netmag1, Stamag1
        event1, origin1, netmag1, Stamag2
        event1, origin1, netmag1, Stamag3
        event1, origin1, netmag2, Stamag4
        event1, origin1, netmag2, Stamag5
        ...
        or
        event1, origin1, assoc1, arrival1
        event1, origin1, assoc2, arrival2
        event1, origin2, assoc3, arrival3
        event1, origin2, assoc4, arrival4
        event2, origin3, assoc5, arrival5
        ...

    resource_prefix : str
        The base string prefixing any quakeml/obspy.Catalog resource IDs.

    Notes
    -----
    The tree has the following structure:
    {
        eventkey1:
        'instance': event1,
        'picks': {
            arrivalkey1: arrival1,
            arrivalkey2, arrival2,
            ...
        }
        'origins': {
            originkey1: {
                'instance': origin1,
                'magnitudes': {
                    netmagkey1: netmag1,
                    netmagkey2: netmag2,
                    ...
                },
                'station_magnitudes': {
                    stamagkey1: stamag1,
                    stamagkey2: stamag2,
                    ...
                },
            'arrivals': {
                assockey1: assoc1,
                assockey2, assoc2,
                ...
                },
            }
        }
    }

    Keys are the (hashable) output of `sqlalchemy.inspect(instance).identity_key`.

    """
    def __init__(self, *event_queries, resource_prefix='smi:local'):
        self.resource_prefix = resource_prefix
        self._tree = dtree()

    def __getitem__(self, key):
        return self._tree[key]

    def __setitem__(self, key, value):
        self._tree[key] = value

    def __delitem__(self, key):
        del self._rtree[key]

    def __str__(self):
        """ Pretty-print the structure of the event tree. """
        indent = 2
        L0 = ''
        L1 = indent * ' '
        L2 = 2 * L1
        L3 = 3 * L1
        L4 = 4 * L1

        tree = self._tree
        out = ''
        for eventkey in tree:
            out += repr(tree[eventkey]['instance']) + os.linesep
            out += L1 + '[picks],[amplitudes]' + os.linesep
            for arrivalkey in tree[eventkey]['picks']:
                out += L2 + repr(tree[eventkey]['picks'][arrivalkey]) + os.linesep
            out += L1 + '[origins]' + os.linesep
            for originkey in tree[eventkey]['origins']:
                out += L2 + repr(tree[eventkey]['origins'][originkey]['instance']) + os.linesep
                out += L3 + '[magnitudes]' + os.linesep
                for netmagkey in tree[eventkey]['origins'][originkey]['magnitudes']:
                    out += L4 + repr(tree[eventkey]['origins'][originkey]['magnitudes'][netmagkey]) + os.linesep
                out += L3 + '[station_magnitudes]' + os.linesep
                for stamagkey in tree[eventkey]['origins'][originkey]['station_magnitudes']:
                    out += L4 + repr(tree[eventkey]['origins'][originkey]['magnitudes'][stamagkey]) + os.linesep
                out += L3 + '[arrivals]' + os.linesep
                for assockey in tree[eventkey]['origins'][originkey]['arrivals']:
                    out += L4 + repr(tree[eventkey]['origins'][originkey]['arrivals'][assockey]) + os.linesep

        return out

    def update(self, query):
        """ Append to or update an event tree using event query results.

        Parameters
        ----------
        query : sqlalchemy.orm.Query

        """
        # We'll turn table row instances into a tree with the following structure that mirrors QuakeML/obspy.Catalog.
        # Each row of the incoming query's result set (e.g.  (event, origin, netmag, assoc, arrival))
        # can be thought of as a path/address into this nested dict. the paths/keys make the structure
        # "immune" to redundancies in the query result rows.

        # event/origin/etc.. instances aren't hashable, so they can't be used directly
        # as dictionary keys in the tree, but SQLAlchemy makes a hashable "identity key"
        # for each instance so that it's identity can be tracked in the session.
        # We use `sqlalchemy.inspect` to get the hashable SQLA key for each instance, and build
        # the tree with it.

        # Whenever a node contains lists of something (e.g. each origin has a list of magnitudes),
        # a text key represents the list, and 'instance' holds the node's instance itself.
        # Leaf nodes (e.g. magnitudes under the 'magnitudes' list/node) simply use their key to
        # store their instance, like:
        #
        #   tree[eventkey]['origins'][originkey]['magnitudes'][netmagkey] = netmag
        #   tree[eventkey]['origins'][originkey]['arrivals'][assockey] = assoc
        #   tree[eventkey]['origins'][originkey]['instance'] = origin
        #   tree[eventkey]['picks'][arrivalkey] = arrival
        #   tree[eventkey]['amplitudes'][arrivalkey] = arrival
        #   tree[eventkey]['instance'] = event

        # If needed, we can use those keys to retrieve the actual instances, like:
        # instance = session.identity_map[key]
        # or
        # instance = query.session.get(Tableclass, identity_key)
        # This works only for instances retrieved from a database, or merged into the session with:
        # `session.merge(instance)`

        tree = self._tree

        table_types = ('Event', 'Origin', 'Netmag', 'Stamag', 'Assoc', 'Arrival')
        Event, Origin, Netmag, Stamag, Assoc, Arrival = _get_entities(query, *table_types)

        if not (Event and Origin):
            msg = "Event and Origin tables must be present in each provided query."
            raise ValueError(msg)

        for row in query:
            # get available instances
            # we use the 'db' prefix to disambiguate database row instances from
            # similarly-named QuakeML elements.

            # these should always be present:
            # event, origin
            event = getattr(row, Event.__name__) # event = row.MyEvent
            eventkey = inspect(event).identity_key
            self._tree[eventkey]['instance'] = event

            origin = getattr(row, Origin.__name__)
            originkey = inspect(origin).identity_key
            self._tree[eventkey]['origins'][originkey]['instance'] = origin

            if Arrival:
                # "picks" in quakeml are like Arrival rows, and they're at the Event level
                arrival = getattr(row, Arrival.__name__)
                arrivalkey = inspect(arrival).identity_key
                self._tree[eventkey]['picks'][arrivalkey] = arrival

                # "amplitudes" info in quakeml are stored in arrival rows, also at the Event level,
                # so we'll also store arrivals in an 'amplitudes' branch
                self._tree[eventkey]['amplitudes'][arrivalkey] = arrival

            if Netmag:
                netmag = getattr(row, Netmag.__name__)
                netmagkey = inspect(netmag).identity_key
                self._tree[eventkey]['origins'][originkey]['magnitudes'][netmagkey] = netmag

            if Stamag:
                stamag = getattr(row, Stamag.__name__)
                stamagkey = inspect(stamag).identity_key
                self._tree[eventkey]['origins'][originkey]['station_magnitudes'][stamagkey] = stamag

            if Assoc:
                # "arrivals" in quakeml are like Assoc rows
                assoc = getattr(row, Assoc.__name__)
                assockey = inspect(assoc).identity_key
                self._tree[eventkey]['origins'][originkey]['arrivals'][assockey] = assoc

    def event(self, event):
        """ Initiate an obspy.core.event.Event from a database Event row. """
        resource_prefix = self.resource_prefix
        qevent = qml.Event(
            resource_id=qml.ResourceIdentifier(id=f'{resource_prefix}/event/event.evid={event.evid}'),
            creation_info=qml.CreationInfo(author=event.auth),
            description=qml.EventDescription(text=event.evname, type="earthquake name"),
        )
        return qevent

    def origin(self, origin):
        """ Initiate an obspy.core.event.Origin from a database Origin row. """
        resource_prefix = self.resource_prefix
        qorigin = qml.Origin(
            resource_id=qml.ResourceIdentifier(id=f'{resource_prefix}/origin/origin.orid={origin.orid}')
        )
        return qorigin

    def pick(self, arrival):
        """ Initialize an obspy.core.event.Pick from a database Arrival row. """
        resource_prefix = self.resource_prefix
        pick = qml.Pick(
            resource_id=qml.ResourceIdentifier(id=f'{resource_prefix}/pick/arrival.arid={arrival.arid}'),
            waveform_id=qml.WaveformStreamID(station_code=arrival.sta, channel_code=arrival.chan),
            time=UTCDateTime(arrival.time),
            time_errors=qml.QuantityError(uncertainty=arrival.deltim),
            horizontal_slowness=arrival.slo,
            horizontal_slowness_errors=qml.QuantityError(uncertainty=arrival.delslo),
            backazimuth=baz if (baz := arrival.azimuth - 180) >= 0 else arrival.azimuth + 180,
            backazimuth_errors=qml.QuantityError(uncertainty=arrival.delaz),
            onset=FDSN_PICK_ONSET.get(arrival.qual, None),
            phase_hint=arrival.iphase,
            polarity=FDSN_POLARITY.get(arrival.fm, None),
        )
        return pick

    def amplitude(self, arrival, resource_prefix, pick_id=None, waveform_id=None):
        """ Initialize an obspy.core.event.Amplitude from a database Arrival row.

        Unfilled:
        - pick_id
        - waveform_id

        """
        resource_prefix = self.resource_prefix
        amp = qml.Amplitude(
            resource_id=qml.ResourceIdentifier(id=f'{resource_prefix}/amplitude/arrival.arid={arrival.arid}'),
            waveform_id=qml.WaveformStreamID(station_code=arrival.sta, channel_code=arrival.chan),
            generic_amplitude=arrival.amp*1e9, #nanometers to meters
            unit='m',
            type='A',
            category='period',
            period=arrival.per,
            snr=arrival.snr,
            magnitude_hint='M',
        )
        return amp

    def magnitude(self, netmag, origin_id=None):
        """ Initialize an obspy.core.event.Magnitude from a database Netmag row. """
        resource_prefix = self.resource_prefix
        magnitude = qml.Magnitude(
            resource_id=qml.ResourceIdentifier(id=f'{resource_prefix}/magnitude/netmag.magid={netmag.magid}'),
            mag=netmag.magnitude,
            type=netmag.magtype,
            station_count=netmag.nsta,
            origin_id=origin_id,
        )
        return magnitude

    def catalog(self, description, comments, preferred_magauth, preferred_magtype):
        """ Convert an database event tree to an obspy Catalog.

        Parameters
        ----------
        tree : ETree
            A dictionary event tree from database data.

        For other parameters, see `catalog` function.

        Returns
        -------
        obspy.core.events.Catalog

        TODO:
        - focal mechanisms
        - station magnitudes

        Examples
        --------
        >>> etree = ETree(event_query1, event_query2, 'smi:my.institute.edu')
        >>> cat = etree.catalog("my catalog", "this was hard to program", ('USGS', 'LANL'), ('Mw', 'mb'))

        """
        # It becomes necessary to distinguish QuakeML "Event" objects from database Event instances.
        # We adopt the "q" prefix to distinguish QuakeML elements from database table rows
        resource_prefix = self.resource_prefix
        cat = qml.Catalog(
            creation_info=qml.CreationInfo(author=f'Pisces v{ps.__version__}', creation_time=UTCDateTime()),
            resource_id=qml.ResourceIdentifier(prefix=f'{resource_prefix}/catalog') # uses a uuid after prefix
        )

        tree = self._tree
        for eventkey in tree:
            event = tree[eventkey]['instance']
            qevent = self.event(event)

            origins = tree[eventkey]['origins']
            for originkey in origins:
                #b/c origin nodes aren't leaf nodes, we need to use 'instance' get the instance
                origin = origins[originkey]['instance']
                qorigin = self.origin(origin)
                qevent.events.append(qorigin)

                if origin.orid == event.prefor:
                    # this as the preferred origin
                    qevent.preferred_origin_id = qorigin.resource_id
                    qevent.event_type = FDSN_EVENT_TYPE.get(event.etype, "not reported")

                netmags = tree['eventkey']['origins'][originkey]['magnitudes']
                for netmagkey in netmags:
                    netmag = netmags[netmagkey]
                    magnitude = self.magnitude(netmag, origin_id=qorigin.resource_id)
                    qevent.magnitudes.append(magnitude)

            # both QML 'picks' and 'amplitudes' information are in Arrival table rows
            arrivals = tree[eventkey]['picks']
            for arrivalkey in arrivals:
                #b/c arrival nodes are leaf nodes, we can just use the key to get the instance
                arrival = arrivals[arrivalkey]
                pick = self.pick(arrival)
                qevent.picks.append(pick)

                amplitude = self.amplitude(arrival)
                amplitude.waveform_id = pick.waveform_id

        return cat



def catalog(*event_queries,
            resource_prefix='smi:local',
            description=None,
            comments=None,
            preferred_magauth=None,
            preferred_magtype=('mw', 'mb', 'ms')
):
    """ Produce an ObsPy Catalog object from event.filter_* query results.

    Parameters
    ----------
    event_queries : sqlalchemy.orm.Query instances
        One or more queries, output from filter_events, filter_arrivals, or filter_magnitudes,
        with any of the following structures (tables in any order):
        query = session.query(Event, Origin) # from filter_events
        query = session.query(Event, Origin, Netmag) # from filter_magnitudes
        query = session.query(Event, Origin, Netmag, Stamag) # from filter_magnitudes
        query = session.query(Event, Origin, Assoc, Arrival) # from filter_arrivals
    resource_prefix : str
        The prefix used when creating ResourceIndentifier ids.
        e.g. 'smi:lanl.gov' will result in 'smi:lanl.gov/event/<evid>' for events, etc...
    description, comments : str
        Passed directly to `obspy.core.event.Catalog` during creation.
    preferred_magtype : str or tuple of str
        CSS-like databases don't have a concept of preferred magnitude, so you can provide a
        prioritized list of magnitude types to help select the preferred magnitude for an event. If
        multiple magnitudes of a given type are recorded, the first magnitude author found in
        `preferred_magauth` will be used. If `preferred_magauth` isn't provided, the first magnitude
        of the given type, whether from the Origin or Netmag table, is chosen.  This option has
        priority over `preferred_magauth` below. Not yet implemented.
    preferred_magauth : str or tuple of str
        CSS-like databases don't have a concept of preferred magnitude, so we provide a prioritized
        list of magnitude authors to help select the preferred magnitude for an event when multiple
        magnitudes are recorded.  If multiple magnitudes with a given author are recorded, the first
        one is selected. If used with the `preferred_magtype`, this option has lower priority.  I
        will only be used if multiple magnitudes of a given type are recorded, but none are in the
        `preferred_magtype`. Not yet implemented.

    Returns
    -------
    obspy.Catalog



    """
    # to get instances back from their identity key:
    # entity, pk, _ = originkey
    # query.session.get(entity, pk)
    # or:
    # query.session.get(originkey[0], originkey[1])


    ETREE = dtree()
    for query in event_queries:
        ETREE = fill_etree(query, tree=ETREE)

    cat = etree_to_catalog(ETREE, resource_prefix, description, comments, preferred_magauth, preferred_magtype)
    # TODO: perform origin time / magnitude sorting here?