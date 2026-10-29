""" Functions in support of query-building modules.
"""


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
