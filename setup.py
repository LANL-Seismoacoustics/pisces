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

setup(name='pisces-db',
    version='0.2.1',
    description='A Practical Seismological Database Library in Python.',
    long_description=open('README.rst').read(),
    author='Jonathan MacCarthy',
    author_email='jkmacc@lanl.gov',
    packages=['pisces','pisces.schema','pisces.io','pisces.tables'],
    url='https://github.com/jkmacc-LANL/pisces',
    keywords = ['seismology', 'geophysics', 'database'],
    install_requires=['numpy','obspy>=0.8','sqlalchemy>=0.7','Click'],
    ext_package='pisces.io.lib',
    ext_modules=[Extension('libecompression', ['pisces/io/src/e_compression/e_compression.c']),
                 Extension('libconvert',glob.glob('pisces/io/src/convert/*.c'))],
    entry_points = """
        [console_scripts]
        pisces=pisces.cli.main:cli
        """,
    #package_data={'pysmo.aimbat': ['ttdefaults.conf', 'Readme.txt', 'Version.txt', 'License.txt', 'Changelog.txt']},
    #'entry_points' = {'console_scripts': ['find_events': 'pisces.scripts.find_events:main',
    #                                      'pisces-find_stations': 'pisces.scripts.find_stations:main',
    #                                      'pisces-sac2db': 'pisces.scripts.sac2db:main'],
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
