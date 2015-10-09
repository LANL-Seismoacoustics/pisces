"""
Command-line interface to common Pisces functionality.

This module imports functions from elsewhere in Pisces, wraps them inside local
functions to perform certain common tasks, and uses Click to provide a
command-line interface.  These interfaces functions are organized under a single
nested interface, which is then exported to the command-line using setuptools
entry_points.

"""
from __future__ import print_function
import click

# import pisces.util as _ut
# from .. import request as req



# ##################### MAIN #################### 
@click.group('pisces')
def cli(**kwargs):
    """
    Pisces command-line interface.

    Gateway to common command-line functionality.

    """
    print("cli: {}".format(kwargs))


# ##################### INIT #################### 
@cli.command('init')
@click.argument('url')
def init(**kwargs):
    """
    Initialize the core tables.

    This is the much longer help for this function.

    """
    print("init: {}".format(kwargs))


# ##################### DROP #################### 
@cli.command('drop')
@click.argument('url')
def drop(**kwargs):
    """
    Drop core tables.

    This is the much longer help for this function.

    """
    print("drop: {}".format(kwargs))


# ##################### SAC2DB #################### 
@cli.command('sac2db')
@click.argument('url')
def sac2db(**kwargs):
    """
    Scrape SAC files into database tables.

    This is the much longer help for this function.

    """
    print("sac2db: {}".format(kwargs))


# ##################### MSEED2DB #################### 
@cli.command('mseed2db')
@click.argument('url')
def mseed2db(**kwargs):
    """
    Scrape MSEED files into database tables.

    This is the much longer help for this function.

    """
    print("mseed2db: {}".format(kwargs))


####################### GET #################### 
# This is where elementary querying is done.
#
@cli.group('query')
def query(**kwargs):
    """
    Perform a query.

    Longer help for this function.

    """
    print("get: {}".format(kwargs))


@query.command('stations')
@click.argument('url')
def query_stations(**kwargs):
    """
    Get stations from site table.

    Much longer help for this function.

    """
    print("stations: {}".format(kwargs))

@query.command('events')
@click.argument('url')
def query_events(**kwargs):
    """
    Get origins from origin table.

    Much longer help for this function.

    """
    print("events: {}".format(kwargs))

@query.command('waveforms')
@click.argument('url')
def query_waveforms(**kwargs):
    """
    Get origins from origin table.

    Much longer help for this function.

    """
    print("waveforms: {}".format(kwargs))


if __name__ == '__main__':
    cli()
