#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" 
Pisces: A Practical Seismological Database Library in Python


"""
try:
    import setuptools
except:
    pass

import os
import inspect
import glob
from numpy.distutils.core import setup, Extension

doclines = __doc__.split("\n")

# also stolen from ObsPy
SETUP_DIRECTORY = os.path.dirname(os.path.abspath(inspect.getfile(
    inspect.currentframe())))

# def find_packages():
#     """
#     Simple function to find all modules under the current folder.
# 
#     Stolen from ObsPy.
#     """
#     modules = []
#     for dirpath, _, filenames in os.walk(os.path.join(SETUP_DIRECTORY,
#             "pisces")):
#         if "__init__.py" in filenames:
#             modules.append(os.path.relpath(dirpath, SETUP_DIRECTORY))
#     return [_i.replace(os.sep, ".") for _i in modules]

# download_url = 'http://github.com/jkmacc-lanl/pisces/tarball/0.2',

setup(name='pisces-db',
    version='0.2.1',
    description='A Practical Seismological Database Library in Python.',
    long_description=open('README.rst').read(),
    author='Jonathan MacCarthy',
    author_email='jkmacc@lanl.gov',
    packages=['pisces','pisces.schema','pisces.io'],
    url='https://github.com/jkmacc-LANL/pisces',
    keywords = ['seismology', 'geophysics', 'database'],
    install_requires=['numpy','obspy>=0.8','sqlalchemy>=0.7'],
    ext_package='pisces.io.lib',
    ext_modules=[Extension('libecompression', ['pisces/io/src/e_compression/e_compression.c']),
         Extension('libconvert',glob.glob('pisces/io/src/convert/*.c'))],
    #package_data={'pysmo.aimbat': ['ttdefaults.conf', 'Readme.txt', 'Version.txt', 'License.txt', 'Changelog.txt']},
    #'entry_points' = {'console_scripts': ['find_events': 'pisces.scripts.find_events:main',
    #                                       find_stations': 'pisces.scripts.find_stations:main',
    #                                       'traces2db': 'pisces.scripts.traces2db:main'],
    license='LANL-MIT',
    platforms=['Mac OS X', 'Linux/Unix'],
    classifiers=['Development Status :: 3 - Alpha',
            'Environment :: Console',
            'Intended Audience :: Science/Research',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Topic :: Scientific/Engineering',
            'Topic :: Database',
            'Topic :: Scientific/Engineering :: Physics'],
)
