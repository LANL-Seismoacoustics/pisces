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

import sac2db
import pisces.request as req

# ------------------------------- MAIN ----------------------------------------
# This is the main function/group.  It does nothing except provide a top-level
# --help and serve as a single point of invocation for other subcommands, like
# the way "git" works.  Also, since click.option doesn't support help=, we
# document common arguments, like URL, in the main function.

@click.group()  # "group" means that the command/function can take sub-commands
def cli(**kwargs):
    """
    Pisces command-line interface.

    Commonly-used functionality is exposed as subcommands of this top-level
    function. See "Commands" for things you can do.  Common ARGS are described
    below.

    \b
    Arguments:
      URL     SQLAlchemy-compatible database URI string.
              e.g. sqlite:///localdb.sqlite
                   oracle://user[:password]@server:port/database
                      (leave out password blank for prompt)
        

    """
    print("cli: {}".format(kwargs))


# ------------------------------- INIT ----------------------------------------
@cli.command('init')
@click.argument('url')
@click.option('-t', help="help!")
def init(**kwargs):
    """
    Initialize the core tables.

    Not yet implemented.

    """
    print("init: {}".format(kwargs))


# ------------------------------- DROP ----------------------------------------
@cli.command('drop')
@click.argument('url')
def drop(**kwargs):
    """
    Drop core tables.

    Not yet implemented.

    """
    print("drop: {}".format(kwargs))


# ------------------------------- SAC2DB --------------------------------------
@cli.command('sac2db')
@click.argument('url')
def sac2db(*args, **kwargs):
    """
    Scrape SAC files into database tables.

    This is the much longer help for this function.

    """
    print("sac2db: {}, {}".format(args, kwargs))


# ------------------------------- MSEED2DB ------------------------------------
@cli.command('mseed2db')
@click.argument('url')
def mseed2db(**kwargs):
    """
    Scrape MSEED files into database tables.

    Not yet implemented.

    """
    print("mseed2db: {}".format(kwargs))


# ------------------------------- QUERY ---------------------------------------
# This is where elementary querying is done, mostly using pisces.request
#
@cli.group('query')
def query(**kwargs):
    """
    Perform a basic query.

    Not yet implemented.

    """
    print("query: {}".format(kwargs))


@query.command('stations')
@click.argument('url')
def query_stations(**kwargs):
    """
    Query stations from the site table.

    Not yet implemented.

    """
    print("stations: {}".format(kwargs))

@query.command('events')
@click.argument('url')
def query_events(**kwargs):
    """
    Query the origin table for events.

    Not yet implemented.

    """
    print("events: {}".format(kwargs))

@query.command('waveforms')
@click.argument('url')
def query_waveforms(**kwargs):
    """
    Query waveforms from the wfdisc table.

    Not yet implemented.

    """
    print("waveforms: {}".format(kwargs))


if __name__ == '__main__':
    cli()
