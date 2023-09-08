"""
from pisces.catalog import ETree

tree = ETree(query1, query2, resource_prefix='smi:lanl.gov')
tree.update(query3)
tree.catalog()

"""
from itertools import zip_longest
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


def pretty(d, out=None, indent=0):
    """ Pretty-print a dict tree.

    Use with os.linesep.join(out)

    """
    out = out or []
    for key, value in d.items():
        if isinstance(key, tuple):
            if 'instance' in value:
                out.append('  ' * indent + repr(value['instance']))
            else:
                out.append('  ' * indent + repr(value))
        elif key == 'instance':
            pass
        else:
            out.append('  ' * indent + str(key))

        if isinstance(value, dict):
           out = pretty(value, out, indent+1)
        else:
            pass

    return out


class ETree:
    """
    Event tree

    Turn redundant tabular data from a database into nonredudant hierarchical data
    that can be easily traversed to produce a QuakeML/obspy.Catalog (see `ETree.catalog`).

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
        event1, origin1, netmag1, stamag1
        event1, origin1, netmag1, stamag2
        event1, origin1, netmag1, stamag3
        event1, origin1, netmag2, stamag4
        event1, origin1, netmag2, stamag5
        ...
        or
        event1, origin1, assoc1/arrival1
        event1, origin1, assoc2/arrival2
        event1, origin2, assoc3/arrival3
        event1, origin2, assoc4/arrival4
        event2, origin3, assoc5/arrival5
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
        eventkey1: {
            'instance': event1,         # quakeml Event
            'origins': {
                originkey1: {
                    'instance': origin1,    # quakeml Origin
                    'assocs': {
                        assockey1: assoc1,  # quakeml Arrival
                        assockey2: assoc2,
                        ...
                    },
                    'arrivals': {
                        arrivalkey1: arrival1,  # quakeml Pick
                        arrivalkey2: arrival2,
                        ...
                    },
                    'netmags': {
                        netmagkey1: {
                            'instance': netmag1, # quakeml Magnitude
                            'stamags': {
                                stamagkey1: stamag1,    # quakeml StationMagnitude
                                stamagkey2: stamag2,
                                ...
                            }
                        }
                    }
                }
            }
        }
    }

    Keys are the (hashable) output of `sqlalchemy.inspect(instance).identity_key`.

    Access parts of the tree like:

    tree[eventkey]['origins'][originkey]['netmags'][netmagkey] = netmag
    tree[eventkey]['origins'][originkey]['assocs'][assockey] = assoc
    tree[eventkey]['origins'][originkey]['instance'] = origin
    tree[eventkey]['arrivals'][arrivalkey] = arrival
    tree[eventkey]['amplitudes'][arrivalkey] = arrival
    tree[eventkey]['instance'] = event

    """
    def __init__(self, *event_queries, resource_prefix='smi:local'):
        self.resource_prefix = resource_prefix
        self._tree = dtree()

        for query in event_queries:
            self.update(query)

    def __str__(self):
        """ Pretty-print the structure of the event tree. """
        out = pretty(self._tree)

        return os.linesep.join(out)

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

            # "picks" in quakeml are like Arrival rows, and they're at the Event level
            # "amplitudes" in quakeml are also stored in Arrival rows, and at the Event level,
            # so we'll ultimately just reuse arrivals for them.
            if Arrival:
                arrival = getattr(row, Arrival.__name__)
                arrivalkey = inspect(arrival).identity_key
                self._tree[eventkey]['origins'][originkey]['arrivals'][arrivalkey] = arrival

            if Assoc:
                # "arrivals" in quakeml are like Assoc rows
                assoc = getattr(row, Assoc.__name__)
                assockey = inspect(assoc).identity_key
                self._tree[eventkey]['origins'][originkey]['assocs'][assockey] = assoc

            # "magnitudes" in quakeml are Netmag rows and are kept at the Event level,
            # but Netmag rows are generally tied to origins. we keep them at Origin level for easier
            # processing later (they're children of their Origin instead of disconnected from them).
            if Netmag:
                netmag = getattr(row, Netmag.__name__)
                netmagkey = inspect(netmag).identity_key
                self._tree[eventkey]['origins'][originkey]['netmags'][netmagkey]['instance'] = netmag

            # "station_magnitudes" in quakeml are Stamag rows, and are kept at the Event level,
            # but Stamag rows are generally also tied to origins.  We'll keep them at Origin level
            # for easier processing later.
            if Stamag:
                stamag = getattr(row, Stamag.__name__)
                stamagkey = inspect(stamag).identity_key
                self._tree[eventkey]['origins'][originkey]['netmags'][netmagkey]['stamags'][stamagkey] = stamag

        return self


    def event(self, event):
        """ Return an obspy.core.event.Event from a database Event row. """
        prefix = self.resource_prefix
        eventkey = inspect(event).identity_key
        tree = self._tree

        qevent = qml.Event(
            resource_id=qml.ResourceIdentifier(id=f'{prefix}/event/event.evid={event.evid}'),
            creation_info=qml.CreationInfo(author=event.auth),
            description=qml.EventDescription(text=event.evname, type="earthquake name"),
        )

        return qevent


    def origin(self, origin):
        """ Return an obspy.core.event.Origin from a database Origin row. """
        prefix = self.resource_prefix
        tree = self._tree
        qorigin = qml.Origin(
            resource_id=qml.ResourceIdentifier(id=f'{prefix}/origin/origin.orid={origin.orid}'),
            time=UTCDateTime(origin.time),
            longitude=origin.lon,
            latitude=origin.lat,
            depth=origin.depth,
        )
        return qorigin


    def pick(self, arrival):
        """ Initialize an obspy.core.event.Pick from a database Arrival row. """
        prefix = self.resource_prefix
        pick = qml.Pick(
            resource_id=qml.ResourceIdentifier(id=f'{prefix}/pick/arrival.arid={arrival.arid}'),
            waveform_id=qml.WaveformStreamID(station_code=arrival.sta, channel_code=arrival.chan),
            time=UTCDateTime(arrival.time),
            time_errors=qml.QuantityError(uncertainty=arrival.deltim),
            horizontal_slowness=arrival.slow,
            horizontal_slowness_errors=qml.QuantityError(uncertainty=arrival.delslo),
            backazimuth=baz if (baz := arrival.azimuth - 180) >= 0 else arrival.azimuth + 180,
            backazimuth_errors=qml.QuantityError(uncertainty=arrival.delaz),
            onset=FDSN_PICK_ONSET.get(arrival.qual, None),
            phase_hint=arrival.iphase,
            polarity=FDSN_POLARITY.get(arrival.fm, None),
        )
        return pick

    def arrival(self, assoc, pick_id=None):
        """ Initialize an obspy.core.event.Arrival from a database Assoc row. """
        prefix = self.resource_prefix
        qarrival = qml.Arrival(
            resource_id=qml.ResourceIdentifier(id=f'{prefix}/arrival/assoc.arid={assoc.arid}'),
            pick_id=pick_id,
            phase=assoc.phase,
            distance=assoc.delta,
            time_residual=assoc.timeres,
            horizontal_slowness_residual=assoc.slores,
            backazimuth_residual=assoc.azres,
        )
        return qarrival


    def amplitude(self, arrival, pick_id=None):
        """ Initialize an obspy.core.event.Amplitude from a database Arrival row. """
        prefix = self.resource_prefix
        amp = qml.Amplitude(
            resource_id=qml.ResourceIdentifier(id=f'{prefix}/amplitude/arrival.arid={arrival.arid}'),
            waveform_id=qml.WaveformStreamID(station_code=arrival.sta, channel_code=arrival.chan),
            pick_id=pick_id,
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
        prefix = self.resource_prefix
        magnitude = qml.Magnitude(
            resource_id=qml.ResourceIdentifier(id=f'{prefix}/magnitude/netmag.magid={netmag.magid}'),
            mag=netmag.magnitude,
            magnitude_type=netmag.magtype,
            station_count=netmag.nsta,
            origin_id=origin_id,
        )
        return magnitude


    def catalog(self, description=None, preferred_magauth=None, preferred_magtype=None):
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
            resource_id=qml.ResourceIdentifier(prefix=f'{resource_prefix}/catalog'), # uses a uuid after prefix
            description=description,
        )

        tree = self._tree
        for eventkey in tree:
            # b/c event nodes aren't leaf nodes (we use its key to get child nodes),
            # we need to use 'instance' get the actual instance
            event = tree[eventkey]['instance']
            # build an obspy Event from a database Event row
            qevent = self.event(event)

            origins = tree[eventkey]['origins']
            for originkey in origins:
                origin = origins[originkey]['instance']
                qorigin = self.origin(origin)
                qevent.origins.append(qorigin)

                if origin.orid == event.prefor:
                    # this as the preferred origin
                    qevent.preferred_origin_id = qorigin.resource_id
                    qevent.event_type = FDSN_EVENT_TYPE.get(origin.etype, "not reported")

                # process parallel lists of Assoc and Arrival rows
                assocs = tree[eventkey]['origins'][originkey]['assocs']
                arrivals = tree[eventkey]['origins'][originkey]['arrivals']
                for assockey, arrivalkey in zip_longest(assocs, arrivals):
                    # if the lists aren't parallel (one list is empty), the key is None
                    # and the database row is an empty defaultdict, which is Falsy
                    if arrival := arrivals[arrivalkey]:
                        qpick = self.pick(arrival)
                        # stored at the Event level.
                        qevent.picks.append(qpick)

                        amplitude = self.amplitude(arrival, pick_id=qpick.resource_id)
                        amplitude.waveform_id = qpick.waveform_id

                    if assoc := assocs[assockey]:
                        qarrival = self.arrival(assoc, pick_id=qpick.resource_id)
                        # stored at the Origin level.
                        qorigin.arrivals.append(qarrival)

                netmags = tree[eventkey]['origins'][originkey]['netmags']
                for netmagkey in netmags:
                    netmag = netmags[netmagkey]['instance']
                    magnitude = self.magnitude(netmag, origin_id=qorigin.resource_id)
                    # stored at the Event level.
                    qevent.magnitudes.append(magnitude)

                # TODO: station_magnitudes/stamags

            cat.events.append(qevent)

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
    obspy.core.events.Catalog

    """
    # to get instances back from their identity key:
    # entity, pk, _ = originkey
    # query.session.get(entity, pk)
    # or:
    # query.session.get(originkey[0], originkey[1])

    event_tree = ETree(*event_queries, resource_prefix=resource_prefix)

    cat = event_tree.catalog(description, preferred_magauth, preferred_magtype)
    # TODO: perform origin time / magnitude sorting here?

    return cat