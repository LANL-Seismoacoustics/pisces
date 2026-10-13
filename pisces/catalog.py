"""
Convert CSS 3.0 / NNSA KB Core database query results into ObsPy Catalog / QuakeML objects.

The main entry point is `catalog`, which accepts the flat, redundant result sets produced by the
`pisces.events.filter_*` functions and returns an `obspy.core.event.Catalog`.

Examples
--------

>>> from pisces.catalog import catalog
>>> cat = catalog(query, resource_prefix='smi:local', description='my catalog')

"""
import warnings

from obspy import UTCDateTime
import obspy.core.event as qml
from sqlalchemy import inspect
from sqlalchemy.orm import object_session

import pisces as ps
from pisces.util import _get_entities


# Convert KB Core etypes to FDSN event types, best good-faith mapping
# These are also used for a backwards mapping below, so where there multiple backwards mappings,
# the final one is preferred/used. Relies on order-preserving dictionaries in Python 3.7+.
FDSN_EVENT_TYPE = {
    "ec": 'chemical explosion',  # chemical explosion",
    "ep": 'explosion',  # probable explosion",
    "ex": 'explosion',  # generic explosion",
    "en": 'nuclear explosion',  # nuclear explosion",
    "mc": 'collapse',  # collapse",
    "me": 'mining explosion',  # coal bump/mining event",
    "mp": 'mining explosion',  # probable mining event",
    "mb": 'rock burst',  # rock burst",
    "qd": 'earthquake',  # damaging earthquake",
    "qp": 'earthquake',  # unknown-probable earthquake",
    "qf": 'earthquake',  # felt earthquake",
    "qt": 'earthquake',  # generic earthquake/tectonic",
    "ge": 'other event',  # geyser",
    "xm": 'meteorite',  # meteroritic origin",
    "xl": 'other event',  # ligts",
    "xo": 'other event',  # odors",
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
    'w': 'questionable',  # weak
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


def _key(row):
    """ Generalize how to get a row's hashable identity, so it can be easily changed. """
    return inspect(row).identity_key


def _denull(result):
    """
    Replace CSS/KBCore null values in a table row with None.
    Useful to avoid unnecessarily verbose QuakeML or JSON serializations.

    The row is first expunged from its session, if any, so that nulling its values can't be
    flushed back to the database as an UPDATE.

    """
    session = object_session(result)
    if session is not None:
        session.expunge(result)

    for c in result.__table__.columns:
        if getattr(result, c.name) == c.info['default']:
            setattr(result, c.name, None)

    return result


class QMLGenerator:
    """ Convert CSS/KBCore database results to QuakeML/Obspy event objects.

    Examples
    --------

    >>> q = QMLGenerator(resource_prefix='smi:lanl.gov')
    >>> e = q.event(my_database_event_row)
    >>> e
    Event:	2012-04-04T14:21:42.300000Z | +41.818,  +79.689 | 4.4  mb | manual
           resource_id: ResourceIdentifier(id="smi:lanl.gov/event/evid=1")
	        event_type: 'not reported'
	     creation_info: CreationInfo(agency_uri=...)
	referred_origin_id: ResourceIdentifier(id=...)

    """
    def __init__(self, resource_prefix='smi:local'):
        self.resource_prefix = resource_prefix


    def event(self, event):
        """ Return an obspy.core.event.Event from a database Event row. """

        event = _denull(event)

        qevent = qml.Event(
            resource_id=qml.ResourceIdentifier(
                id=f'{self.resource_prefix}/event/event.evid={event.evid}'
            ),
            creation_info=qml.CreationInfo(author=event.auth),
            description=qml.EventDescription(
                text=event.evname,
                # type="earthquake name",
            ),
        )

        return qevent

    def origin(self, origin):
        """ Return an obspy.core.event.Origin from a database Origin row. """
        origin = _denull(origin)
        qorigin = qml.Origin(
            resource_id=qml.ResourceIdentifier(
                id=f'{self.resource_prefix}/origin/origin.orid={origin.orid}'),
            time=UTCDateTime(origin.time),
            longitude=origin.lon,
            latitude=origin.lat,
            depth=origin.depth,
        )
        return qorigin

    def pick(self, arrival):
        """ Initialize an obspy.core.event.Pick from a database Arrival row. """
        arrival = _denull(arrival)
        fields = {
            "resource_id": qml.ResourceIdentifier(
                id=f'{self.resource_prefix}/pick/arrival.arid={arrival.arid}'),
            "waveform_id": qml.WaveformStreamID(
                station_code=arrival.sta, channel_code=arrival.chan),
            "time": UTCDateTime(arrival.time),
            "onset": FDSN_PICK_ONSET.get(arrival.qual),
            "phase_hint": arrival.iphase,
            "polarity": FDSN_POLARITY.get(arrival.fm),
        }
        if arrival.deltim is not None:
            fields["time_errors"] = qml.QuantityError(uncertainty=arrival.deltim)
        if arrival.slow is not None:
            fields["horizontal_slowness"] = arrival.slow
        if arrival.delslo is not None:
            fields["horizontal_slowness_errors"] = qml.QuantityError(
                uncertainty=arrival.delslo)
        if arrival.azimuth is not None:
            fields["backazimuth"] = (arrival.azimuth + 180) % 360
        if arrival.delaz is not None:
            fields["backazimuth_errors"] = qml.QuantityError(uncertainty=arrival.delaz)
        return qml.Pick(**fields)

    def arrival(self, assoc, pick_id=None):
        """ Initialize an obspy.core.event.Arrival from a database Assoc row. """
        assoc = _denull(assoc)
        qarrival = qml.Arrival(
            resource_id=qml.ResourceIdentifier(
                id=f'{self.resource_prefix}/arrival/assoc.arid={assoc.arid}'),
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
        arrival = _denull(arrival)
        fields = {
            "resource_id": qml.ResourceIdentifier(
                id=f'{self.resource_prefix}/amplitude/arrival.arid={arrival.arid}'),
            "waveform_id": qml.WaveformStreamID(
                station_code=arrival.sta, channel_code=arrival.chan),
            "pick_id": pick_id,
            "unit": "m",
            "type": "A",
            "category": "period",
            "magnitude_hint": "M",
        }
        if arrival.amp is not None:
            fields["generic_amplitude"] = arrival.amp * 1e-9  # nanometers to meters
        if arrival.per is not None:
            fields["period"] = arrival.per
        if arrival.snr is not None:
            fields["snr"] = arrival.snr
        return qml.Amplitude(**fields)

    def magnitude(self, netmag, origin_id=None):
        """ Initialize an obspy.core.event.Magnitude from a database Netmag row. """
        netmag = _denull(netmag)
        magnitude = qml.Magnitude(
            resource_id=qml.ResourceIdentifier(
                id=f'{self.resource_prefix}/magnitude/netmag.magid={netmag.magid}'),
            mag=netmag.magnitude,
            magnitude_type=netmag.magtype,
            station_count=netmag.nsta,
            origin_id=origin_id,
        )
        return magnitude

    def station_magnitude(self, stamag, origin_id=None, amplitude_id=None):
        """Initialize an obspy.core.event.StationMagnitude from a database Stamag row."""
        stamag = _denull(stamag)
        fields = {
            "resource_id": qml.ResourceIdentifier(
                id=f"{self.resource_prefix}/stationmagnitude/stamag.ampid={stamag.ampid}"),
            "origin_id": origin_id,
            "mag": stamag.magnitude,
            "station_magnitude_type": stamag.magtype,
            "amplitude_id": amplitude_id,
            "waveform_id": qml.WaveformStreamID(station_code=stamag.sta),
        }
        if stamag.uncertainty is not None:
            fields["mag_errors"] = qml.QuantityError(uncertainty=stamag.uncertainty)
        return qml.StationMagnitude(**fields)

    def catalog(self, description=None, comments=None, preferred_magauth=None, preferred_magtype=None):
        """ Initialize an empty obspy Catalog.

        Returns a Catalog with creation info and resource id set, and no events. Events are added by
        the module-level `catalog` function.

        Parameters
        ----------
        description : str
            Passed directly to `obspy.core.event.Catalog` during creation.
        comments : list of obspy.core.event.Comment
            Passed directly to `obspy.core.event.Catalog` during creation.
        preferred_magauth, preferred_magtype : str or tuple of str [not implemented]

        Returns
        -------
        obspy.core.events.Catalog
            An empty catalog.

        TODO:
        - focal mechanisms
        - station magnitudes

        Examples
        --------
        >>> qgen = QMLGenerator(resource_prefix='smi:my.institute.edu')
        >>> cat = qgen.catalog(description="my catalog")

        """
        # preferred_magtype : str or tuple of str [not implemented]
        # CSS-like databases don't have a concept of preferred magnitude, so you can provide a
        # prioritized list of magnitude types to help select the preferred magnitude for an event. If
        # multiple magnitudes of a given type are recorded, the first magnitude author found in
        # `preferred_magauth` will be used. If `preferred_magauth` isn't provided, the first magnitude
        # of the given type, whether from the Origin or Netmag table, is chosen.  This option has
        # priority over `preferred_magauth` below. Not yet implemented.
        # preferred_magauth : str or tuple of str [not implemented]
        # CSS-like databases don't have a concept of preferred magnitude, so we provide a prioritized
        # list of magnitude authors to help select the preferred magnitude for an event when multiple
        # magnitudes are recorded.  If multiple magnitudes with a given author are recorded, the first
        # one is selected. If used with the `preferred_magtype`, this option has lower priority.  I
        # will only be used if multiple magnitudes of a given type are recorded, but none are in the
        # `preferred_magtype`. Not yet implemented.

        # It becomes necessary to distinguish QuakeML "Event" objects from database Event instances.
        # We adopt the "q" prefix to distinguish QuakeML elements from database table rows
        cat = qml.Catalog(
            creation_info=qml.CreationInfo(
                author=f'Pisces v{ps.__version__}', creation_time=UTCDateTime()),
            resource_id=qml.ResourceIdentifier(
                prefix=f'{self.resource_prefix}/catalog'),  # uses a uuid after prefix
            description=description,
            comments=comments,
        )

        return cat


def catalog(*queries,
    resource_prefix='smi:local',
    description=None,
    comments=None,
    preferred_magauth=None,
    preferred_magtype=('mw', 'mb', 'ms')
):
    """
    Build an ObsPy Catalog from one or more CSS/KBCore database result sets.

    Query results are flat and redundant: a joined row repeats its parent values once per child, so
    the same Event appears on every row of its Origins, the same Origin on every row of its Netmags,
    and so on. This function walks each result set once, converting each distinct database row to
    its QuakeML counterpart the first time that row is seen and reusing it thereafter, so repeated
    rows collapse into a single QuakeML object.

    Rows are the unit of correspondence: Assoc/Arrival and Netmag/Stamag that arrive together on one
    row are related to each other, and are linked accordingly.

    Multiple queries accumulate into one catalog. A query whose rows reference an Event or Origin
    already seen in an earlier query merges into that existing QuakeML object rather than
    duplicating it, so related result sets (events, then arrivals, then magnitudes) can be combined.

    Parameters
    ----------
    queries : sqlalchemy.orm.Query instances
        One or more queries, output from filter_events, filter_arrivals, or filter_magnitudes,
        with any of the following structures (tables in any order):
        query = session.query(Event, Origin) # from filter_events
        query = session.query(Event, Origin, Netmag) # from filter_magnitudes
        # from filter_magnitudes
        query = session.query(Event, Origin, Netmag, Stamag)
        # from filter_arrivals
        query = session.query(Event, Origin, Assoc, Arrival)
        Event and Origin must be present in every query.
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
    obspy.core.event.Catalog
        Events in the order first encountered. Empty if no queries are provided.

    Raises
    ------
    ValueError
        If a query doesn't include both an Event and an Origin table.

    Notes
    -----
    Incoming rows look like the following, which is the redundancy this function collapses. Note how
    parent values repeat down each block:

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

    Stamag rows always create QuakeML StationMagnitudes. Their same-row Netmag receives a
    StationMagnitudeContribution only when ``magdef == 'd'``; it has ``weight=1.0`` and maps
    ``magres`` to ``residual``. ``magdef == 'n'`` creates no contribution. Any other value emits a
    warning and creates no contribution. Stamag amplitude links use ``arid`` to reference the
    existing Arrival-derived QuakeML Amplitude; CSS/KBCore ``ampid`` is not currently supported.

    Examples
    --------
    >>> cat = catalog(event_query, resource_prefix='smi:lanl.gov', description='my catalog')
    >>> cat = catalog(event_query, arrival_query)  # merged into one catalog

    """
    qgen = QMLGenerator(resource_prefix=resource_prefix)
    cat = qgen.catalog(description=description, comments=comments)

    # Flat {database row identity: QuakeML object} maps, one per QuakeML type, shared across all
    # queries so a later query referencing an earlier query's event merges into it.
    # De-duplication and QuakeML construction happen together, in a single pass per query, so raw
    # database rows are never retained past the row that produced them.
    qevents = {}
    qorigins = {}
    qpicks = {}
    qamplitudes = {}
    qamplitudes_by_arid = {}
    qmagnitudes = {}
    qstation_magnitudes = {}
    qcontributions = set()

    table_types = ('Event', 'Origin', 'Netmag', 'Stamag', 'Assoc', 'Arrival')

    for query in queries:
        Event, Origin, Netmag, Stamag, Assoc, Arrival = _get_entities(query, *table_types)

        if not (Event and Origin):
            msg = "Event and Origin tables must be present in each provided query."
            raise ValueError(msg)

        for row in query:
            # Rows are redundant: the same event/origin/netmag appears on many rows. Each is
            # converted the first time it's seen, and looked up by identity thereafter.
            # The "q" prefix distinguishes QuakeML elements from database table rows.

            # Event and Origin are always present.
            event = getattr(row, Event.__name__)  # event = row.MyEvent
            eventkey = _key(event)
            if not (qevent := qevents.get(eventkey)):
                # same as: qevent = qevents[eventkey] = qgen.event(event)
                qevent = qgen.event(event)
                qevents[eventkey] = qevent
                cat.events.append(qevent)

            origin = getattr(row, Origin.__name__)
            originkey = _key(origin)
            if not (qorigin := qorigins.get(originkey)):
                # same as: qorigin = qorigins[originkey] = qgen.origin(origin)
                qorigin = qgen.origin(origin)
                qorigins[originkey] = qorigin
                qevent.origins.append(qorigin)

                if origin.orid == event.prefor:
                    # this is the preferred origin
                    qevent.preferred_origin_id = qorigin.resource_id
                    qevent.event_type = FDSN_EVENT_TYPE.get(origin.etype, "not reported")

            # Assoc/Arrival and Netmag/Stamag arrive together on the same row, and the join
            # guarantees that same-row pairs correspond. Children below therefore reference the
            # parent built or found just above, in this row's local scope.

            # QuakeML "picks" and "amplitudes" are both CSS Arrival rows, stored at the Event level.
            qpick = None
            qamplitude = None
            if Arrival:
                arrival = getattr(row, Arrival.__name__)
                arrivalkey = _key(arrival)
                if not (qpick := qpicks.get(arrivalkey)):
                    # same as: qpick = qpicks[arrivalkey] = qgen.pick(arrival)
                    qpick = qgen.pick(arrival)
                    qpicks[arrivalkey] = qpick
                    qevent.picks.append(qpick)

                if not (qamplitude := qamplitudes.get(arrivalkey)):
                    qamplitude = qgen.amplitude(arrival, pick_id=qpick.resource_id)
                    qamplitude.waveform_id = qpick.waveform_id
                    qamplitudes[arrivalkey] = qamplitude
                    qamplitudes_by_arid[arrival.arid] = qamplitude
                    qevent.amplitudes.append(qamplitude)

            # QuakeML "arrivals" are CSS Assoc rows, stored at the Origin level.
            if Assoc:
                assoc = getattr(row, Assoc.__name__)
                qarrival = qgen.arrival(
                    assoc,
                    pick_id=qpick.resource_id if qpick else None,
                )
                qorigin.arrivals.append(qarrival)

            # QuakeML "magnitudes" are Netmag rows, stored at the Event level.
            qmagnitude = None
            if Netmag:
                netmag = getattr(row, Netmag.__name__)
                netmagkey = _key(netmag)
                if not (qmagnitude := qmagnitudes.get(netmagkey)):
                    # same as: qmagnitude = qmagnitudes[netmagkey] = qgen.magnitude(...)
                    qmagnitude = qgen.magnitude(netmag, origin_id=qorigin.resource_id)
                    qmagnitudes[netmagkey] = qmagnitude
                    qevent.magnitudes.append(qmagnitude)

            if Stamag:
                stamag = getattr(row, Stamag.__name__)
                stamagkey = _key(stamag)
                magdef = stamag.magdef
                magres = stamag.magres
                qamplitude = qamplitudes_by_arid.get(stamag.arid)
                amplitude_id = qamplitude.resource_id if qamplitude else None
                if not (qstation_magnitude := qstation_magnitudes.get(stamagkey)):
                    qstation_magnitude = qgen.station_magnitude(
                        stamag,
                        origin_id=qorigin.resource_id,
                        amplitude_id=amplitude_id,
                    )
                    qstation_magnitudes[stamagkey] = qstation_magnitude
                    qevent.station_magnitudes.append(qstation_magnitude)
                elif amplitude_id is not None and qstation_magnitude.amplitude_id is None:
                    qstation_magnitude.amplitude_id = amplitude_id

                if qmagnitude and (contribution_key := (netmagkey, stamagkey)) not in qcontributions:
                    if magdef == "d":
                        qmagnitude.station_magnitude_contributions.append(
                            qml.StationMagnitudeContribution(
                                station_magnitude_id=qstation_magnitude.resource_id,
                                residual=magres,
                                weight=1.0,
                            )
                        )
                    elif magdef != "n":
                        warnings.warn(
                            f"Stamag magdef {magdef!r} is neither 'd' nor 'n'; "
                            "omitting StationMagnitudeContribution.",
                            stacklevel=2,
                        )
                    qcontributions.add(contribution_key)

    return cat
