""" Functions in support of query-building modules.
"""
import sqlalchemy as sa


def make_wildcard_list(toList):
    """
    Take a list, tuple, or comma separated string of variables and output a list
    with sql wildcards '%' and '_'

    Parameters
    ----------
    toList : list, tuple, or comma separated string or variables

    Returns
    -------
    nowList: list of variables contained in the toList variable

    """

    # check if toList is a list and if not, make it a list
    if type(toList) is list:
        nowList = toList

    elif type(toList) is tuple:
        nowList = list(toList)

    elif type(toList) is str:
        nowList = toList.split(',')
    else:
        raise TypeError('input to function make_wildcard_list is not a list, tuple, or comma separated string of variables')

    for x in range(len(nowList)):
       nowList[x] = nowList[x].replace('*','%')
       nowList[x] = nowList[x].replace('?','_')

    return nowList


def range_filters(*restrictions):
    """Restrict a column to a range.

    Parameters
    ----------
    restrictions : iterable of (ORM column, minvalue, maxvalue) tuples

    Returns
    -------
    list of SQLAlchemy filter conditions that can be unpacked into an SQLAlchemy
    filter method, like query.filter(*filters) for AND clauses,
    or query.filter(or_(*filters)) for OR clauses.

    # e.g.
    >>> f = range_filters((Origin.lat, -10, 15), (Origin.depth, None, 80))
    Produces a list containing zero or one filter expressions.
    It's supplied as a list so it can be applied to a query like:
    >>> query.filter(*f)
    which works even if the list is empty (all ranges are None).

    """
    filters = []
    for column, mn, mx in restrictions:
        if mn is not None:
            if mx is not None:
                filters.append(column.between(mn, mx))
            else:
                filters.append(mn <= column)
        elif mx is not None:
            filters.append(column <= mx)

    return filters


def distance_filter(
    big_query, small_query, degrees=None, kilometers=None, yield_per=None, inverse=False
):
    """
    Return a buffered (yield_per) cartesian product of station (includes Site
    table) query and event query (includes Origin table) results, censored to
    include only those within (or outside of) the provided distance ranges.

    Parameters
    ----------
    big_query : SQLAlchemy query
        Query whos results you expect to be the larger of the two.
        This can be batch-realized with the yield_per keyword.
    small_query : SQLAlchemy query
        Query whos results you expect to be the smaller of the two.
        This will be fully realized in-memory.
    degrees, kilometers : tuple (minradius, maxradius) in degrees, kilometers
        Values may include None (unbounded).
        Both keywords can't be used simultaneously.
    yield_per : int
        Buffer size (joined rows) of the distance calculation.
        If None, all results are realized in memory and returned immediately.
    inverse : bool
        If True, return results that are _outside_ the provided distance ranges.

    Returns
    -------
    list or generator
        If `yield_per` is provided, results are a generator that iterates to yield
        an unknown number list of joined result rows that pass the distance filter
        per iteration, internally processing `yield_per` joined rows at a time.
        If `yield_per` is None, a list of filtered results is returned directly.

    Notes
    -----
    Because this filter must realize query results and do a cartesian join on
    them, it's safest to batch process the results. This argument specifies the
    number of rows processed at a time. SQLAlchemy and Oracle, for example, are
    capable of working with a few thousand results at a time on a reasonable
    machine, depending on how many joined tables are already in the query
    objects provided.  Because the function realizes actual query results, the
    queries provided must be "complete" (i.e. include all the intended SQLAlchemy filters).

    def km_distfn(rows, distrange):
        lat0, lon0 = row[0].lat, row[0].lon
        lat1, lon1 = row[1].lat, row[1].lon
        # calculate kilometers stuff
        return distrange[0] <= dist_value <= distrange[1]

    def deg_distfn(rows, distrange):
        lat0, lon0 = row[0].lat, row[0].lon
        lat1, lon1 = row[1].lat, row[1].lon
        # calculate degrees stuff
        return distrange[0] <= dist_value <= distrange[1]

    # this is an iterator that returns one results row at a time.
    # if yield_per was used, it returns a list of result rows at a time.
    return filter(distfn, query)

    """
    pass

def glob_to_like(text, escape='\\'):
    """
    Replace FDSN wildcards to equivalent SQL wildcards.

    Replace '*' or '?' glob characters with SQL '%' or '_' LIKE characters,
    escaping any existing literal '%' or '_' characters.

    """
    # TODO: rename fdsn2sql_glob?
    text = text.replace('_', escape + '_').replace('?', '_')
    text = text.replace('%', escape + '%').replace('*', '%')

    return text


def has_sql_wildcards(text, escape='\\'):
    """ Test for non-escaped '_' or '%' SQL wildcard characters in a string.
    """
    # XXX: fails for '_HZ,B\\_Z' ?
    has_wildcards = ('_' in text and escape + '_' not in text) or \
                    ('%' in text and escape + '%' not in text)

    return has_wildcards


def string_expression(selectable, string_filters):
    """
    Produce a SQLAlchemy filter clause on a given string-type column for a
    list of string patterns.

    Produces LIKE statements if wildcards are present, IN when a list is present,
    == when a single non-wildcarded string is present.  Lists may be comma-separated
    strings.

    Takes a SQLAlchemy selectable (e.g. Site.sta) and a list of strings (e.g.
    ['MDJ']) and creates the appropriate SQL filter expression on the provided
    selectable. The string patterns may include LIKE characters '_' and '%'.

    Parameters
    ----------
    selectable : sqlalchemy.orm.attributes.InstrumentedAttribute
        This is simply an ORM Table string-type column, like Site.sta
    string_filters : list of str
        List of one or more strings for subsetting, which may include SQL LIKE
        characters '_' and '%'.  e.g. ['BHZ'], ['%Z', 'BH_'].
        The easiest way to get this for a string list that may be comma separated
        (e.g. '%Z,B_N') is to always use '%Z,B_N'.split(',').

    Returns
    -------
    expression : SQLAlchemy expression
        An expression to be applied with query.filter(expression).  Equivalent
        to a SQL EQUAL, IN, LIKE statement, or an OR statement containing
        EQUAL, IN, or LIKE statements.

    Examples
    --------
    >>> from pisces.tables.css3 import Wfdisc
    >>> channels = ['%Z', 'B_N', 'HHT']
    >>> chan_expr = string_expression(Wfdisc.chan, channels)
    >>> literal_sql(session.bind, chan_expr) # just shows the literal compiled SQL
    "wfdisc.chan LIKE '%Z' OR wfdisc.chan LIKE 'B_N' OR wfdisc.chan = 'HHT'"
    >>> wfdisc_rows = session.query(Wfdisc).filter(chan_expr).all()

    """
    string_filters = string_filters.split(',') if isinstance(string_filters, str) else string_filters

    if len(string_filters) == 1:
        # don't use OR or IN
        string_filter = string_filters[0]
        if has_sql_wildcards(string_filter):
            expression = selectable.like(string_filter)
        else:
            expression = selectable == string_filter
    else:
        # use OR (for wildcards) or IN
        if any([has_sql_wildcards(string_filter) for string_filter in string_filters]):
            # can't use IN, must use LIKE with OR
            # produces query.filter(or_(selectable.like(thing1), selectable == thing2, ...))
            clauses = [selectable.like(string_filter) if has_sql_wildcards(string_filter)
                       else selectable == string_filter
                       for string_filter in string_filters]
            expression = sa.or_(*clauses)
        else:
            # no wildcards, can just use in_
            expression = selectable.in_(string_filters)

    return expression
