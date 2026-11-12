# FDSN Format Compatibility

Pisces supports FDSN-compatible formats like miniSEED, QuakeML, and StationXML.

It can do this through the `pisces.events` module, or through the `pisces.fdsn.Client` class.

## Event origins and magnitudes

`Client.get_events()` treats `Netmag` as the authoritative source for catalog
magnitudes. Applications using Pisces should propagate supported origin magnitude
values (`mb`, `ml`, and `ms`) into the corresponding `Netmag` rows.

The `includeallorigins` and `includeallmagnitudes` parameters are independent:

- `includeallorigins=False` returns the event's preferred origin only.
- `includeallorigins=True` retains all matching origins, including origins with
  no corresponding `Netmag` row.
- `includeallmagnitudes=False` (the default) includes only the preferred
  magnitude for the event's preferred origin. Other returned origins remain in
  the Catalog but have no attached magnitudes.
- `includeallmagnitudes=True` includes all available `Netmag` rows for the
  returned origins.

An origin with no `Netmag` is still represented in the QuakeML Catalog; it is
simply represented without a QuakeML `Magnitude` object. If magnitudes are
expected in a catalog, the database must contain the corresponding `Netmag`
rows.

## Export QuakeML with the `events` module

First, query
```python

```
