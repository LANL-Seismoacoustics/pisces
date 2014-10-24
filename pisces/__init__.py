# coding: utf-8
"""
Pisces is a practical and extensible data management library in Python.  It 
leverages existing widely-used free and open-source technologies, such as SQL 
databases and Python, in order to provide a seismological data management 
solution that: 

1) allows the user to both manage and analyze data with a single easy-to-learn 
    language, Python, 
2) leverages large existing user communities to facilitate adoption and 
    problem solving in code development, and 
3) imposes no expensive or restrictive licensing constraints on users.  

The ultimate goal of Pisces is to allow the user to write code that will not 
eventually have to be abandoned due to different project scales, system 
architectures, or budgetary and licensing concerns.  

"""

__version__ = '0.2'

from pisces.util import db_connect, get_tables, travel_times
from pisces.schema.util import copy_metadata, string_formatter
#from pisces.io.flatfile import read_flatfile, format_records
from pisces.io.trace import wfdisc2trace
from pisces.schema import kbcore
from pisces.io.readwaveform import read_waveform
