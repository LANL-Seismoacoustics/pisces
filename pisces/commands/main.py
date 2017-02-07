"""
Command-line interface to common Pisces functionality.

This module imports functions from elsewhere in Pisces, wraps them inside local
functions to perform certain common tasks, and uses Click to provide a
command-line interface.  These interfaces functions are organized under a single
nested interface, which is then exported to the command-line using setuptools
entry_points.


DEVELOPERS:
To add a subcommand to the main command, do the following:
1. Add a module file in pisces/commands/ for your implementation
2. Program your functionality into a single function in your modules, and
   import it here.  The module should really just be an ordering of Pisces
   library functions/classes.  The Pisces library functions/classes work with
   native Python objects. The commands submodules do the business of converting
   command-line arguments to a useful form for those library functions.
3. Write a wrapper function for your implementation function here,
   and decorate it with Click.  The docstring for this wrapper function is the
   one that is exposed at the command-line.
   @cli.command('command_name') adds a new "pisces command_name"
   @cli.group('subcommand_name') adds a new "pisces subcommand_name" subcommand

"""

import click

from pisces import __version__
from pisces.util import url_connect
from pisces.commands import sac2db

def split_commas(ctx, param, value):
    """
    Convert from a comma-separated list to a true list.

    """
    # ctx, param, value is the required calling signature for a Click callback
    try:
        values = value.split(',')
    except AttributeError:
        # values is None
        values = None

    return values


# ------------------------------- MAIN ----------------------------------------
# This is the main function/group.  It does nothing except provide a top-level
# --help and serve as a single point of invocation for other subcommands, like
# the way "git" works.  Also, since click.option doesn't support help=, we
# document common arguments, like URL, in the main function.

# "group" means that the command/function can take sub-commands
@click.group(context_settings={'help_option_names': ['-h', '--help']})
@click.version_option(__version__, '-V', '--version')
def cli():
    """
    Pisces command-line interface.

    Commonly-used functionality is exposed as subcommands of this top-level
    function. See "Commands" for things you can do.  Common ARGS are described
    below.

    \b
    Arguments:
      DB      SQLAlchemy-compatible database URI string.
              e.g. sqlite:///localdb.sqlite
                   oracle://user[:password]@server:port/database
                      (leave out password blank for prompt)
              May also be defined as an environmental variable PISCESDB.
        

    """
    pass


# ------------------------------- INIT ----------------------------------------
@cli.command('create')
@click.argument('DB')
def create_command(**kwargs):
    """
    Create core tables.

    Not yet implemented.

    """
    print("create: {}".format(kwargs))


# ------------------------------- DROP ----------------------------------------
@cli.command('drop')
@click.argument('DB')
def drop_command(**kwargs):
    """
    Drop core tables.

    Not yet implemented.

    """
    print("drop: {}".format(kwargs))


# ------------------------------- SAC2DB --------------------------------------
@cli.command('sac2db')
@click.argument('DB', envvar='PISCESDB')
@click.option('-t', '--tables',
              help=("Comma-separated (no spaces), list of tables to create.  "
                    "Default is all core tables with standard names."),
              metavar="owner.tablename[,...]",
              callback=split_commas)
@click.option('-p', '--prefix', default="",
              help=("Target tables using 'account.prefix naming.  "
                    "e.g. myaccount.test_ will target tables like "
                    "myaccount.test_origin, myaccount.test_sitechan."))
@click.option('-A', '--absolute_paths', is_flag=True,
              help=("If set, write database 'dir' directory entries as"
                    " absolute paths, not relative."))
@click.option('--bbfk', is_flag=True,
              help=("If set, get site.deast and dnorth from SAC user7 & user8"
                    " header fields."))
@click.option('-l', '--file_list', type=click.File('r'),
              help="A list file, one file name per line.")
@click.argument('files', nargs=-1, type=click.Path())
def sac2db_command(**kwargs):
    """
    Scrape SAC files into database tables.

    SAC files may be used to produce the following tables: Wfdisc, Site,
    Sitechan, Origin, Event, Arrival, Assoc, Lastid, and Instrument.  Id
    numbering will follow the Lastid table, if one is found, otherwise it will
    start from 1.

    Examples
    --------
    # use standard table names to local test.sqlite file
    pisces sac2db sqlite:///test.sqlite datadir/*.sac

    # prefix all tables in an oracle account with prefix my_, prompt for password
    pisces sac2db --prefix my_ oracle://user@server.domain.com:port/dbname datadir/*.sac

    # if there are too many SAC files for the shell to handle, use a list:
    find datadir -name "*.sac" -print > saclist.txt
    sac2db.py sqlite:///test.sqlite saclist.txt

    """
    # common local functions
    session = url_connect(kwargs['db'])

    # command-specific funtions
    sac2db.main(session=session, **kwargs)


# ------------------------------- MSEED2DB ------------------------------------
@cli.command('mseed2db')
@click.argument('DB')
def mseed2db_command(**kwargs):
    """
    Scrape MSEED files into database tables.

    Not yet implemented.

    """
    print("mseed2db: {}".format(kwargs))


# ------------------------------- QUERY ---------------------------------------
# This is where elementary querying is done, mostly using pisces.request
#
@cli.group('query')
@click.argument('DB')
def query(**kwargs):
    """
    Perform a basic query.

    Not yet implemented.

    """
    print("query: {}".format(kwargs))


@query.command('stations')
@click.argument('DB')
def query_stations(**kwargs):
    """
    Query stations from the site table.

    Not yet implemented.

    """
    print("stations: {}".format(kwargs))

@query.command('events')
@click.argument('DB')
def query_events(**kwargs):
    """
    Query the origin table for events.

    Not yet implemented.

    """
    print("events: {}".format(kwargs))

@query.command('waveforms')
@click.argument('DB')
def query_waveforms(**kwargs):
    """
    Query waveforms from the wfdisc table.

    Not yet implemented.

    """
    print("waveforms: {}".format(kwargs))


if __name__ == '__main__':
    cli()
