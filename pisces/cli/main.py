"""
Command-line interface to common Pisces functionality.

This module imports functions from elsewhere in Pisces, wraps them inside local
functions to perform certain common tasks, and uses Click to provide a
command-line interface.  These interfaces functions are organized under a single
nested interface, which is then exported to the command-line using setuptools
entry_points.

"""

# Developers:
# To add a subcommand to the main command, do the following:
# 1. Add a module file in pisces/cli/ to do your implementation
# 2. Import useful Pisces or other functions into your module
# 3. Program your functionality into a single function, and import it here.
# 4. Write a wrapper function for your implementation function here,
#    and decorate it with click.  The docstring for this wrapper function is the
#    one that is exposed at the command-line.
#    @cli.command('command_name') adds a new "pisces command_name"
#    @cli.group('subcommand_name') adds a new "pisces subcommand_name" subcommand

import click

# ------------------------------- MAIN ----------------------------------------
# This is the main function/group.  It does nothing except provide a top-level
# --help and serve as a single point of invocation for other subcommands, like
# the way "git" works.  Also, since click.option doesn't support help=, we
# document common arguments, like URL, in the main function.
@click.group()
def cli(**kwargs):
    """
    Pisces command-line interface.

    Commonly-used functionality is exposed as subcommands of this top-level
    function.

    \b
    Arguments:
      URL     SQLAlchemy-compatible database URI string.
              e.g. sqlite:///localdb.sqlite
                   oracle://user@server:port/database
        

    """
    print("cli: {}".format(kwargs))


# ------------------------------- INIT ----------------------------------------
@cli.command('init')
@click.argument('url')
@click.option('-t', help="help!")
def init(**kwargs):
    """
    Initialize the core tables.

    This is the much longer help for this function.

    """
    print("init: {}".format(kwargs))


# ------------------------------- DROP ----------------------------------------
@cli.command('drop')
@click.argument('url')
def drop(**kwargs):
    """
    Drop core tables.

    This is the much longer help for this function.

    """
    print("drop: {}".format(kwargs))


# ------------------------------- SAC2DB --------------------------------------
@cli.command('sac2db')
@click.argument('url')
def sac2db(**kwargs):
    """
    Scrape SAC files into database tables.

    This is the much longer help for this function.

    """
    print("sac2db: {}".format(kwargs))


# ------------------------------- MSEED2DB ------------------------------------
@cli.command('mseed2db')
@click.argument('url')
def mseed2db(**kwargs):
    """
    Scrape MSEED files into database tables.

    This is the much longer help for this function.

    """
    print("mseed2db: {}".format(kwargs))


# ------------------------------- QUERY ---------------------------------------
# This is where elementary querying is done, mostly using pisces.request
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
