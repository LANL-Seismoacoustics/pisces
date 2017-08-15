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
import glob
from numpy.distutils.core import setup, Extension

try:
    import pypandoc
    long_description=pypandoc.convert('README.md', 'rst').read()
except ImportError:
    long_description=open('README.md').read()


doclines = __doc__.split("\n")

setup(name='pisces',
    version='0.2.4',
    description='A Practical Seismological Database Library in Python.',
    long_description=long_description,
    author='Jonathan MacCarthy',
    author_email='jkmacc@lanl.gov',
    packages=['pisces','pisces.schema','pisces.io','pisces.tables',
              'pisces.commands'],
    url='https://github.com/jkmacc-LANL/pisces',
    download_url='https://github.com/jkmacc-LANL/pisces/tarball/0.2.2',
    keywords = ['seismology', 'geophysics', 'database'],
    install_requires=['numpy','obspy>=1.0','sqlalchemy>=0.9','Click'],
    ext_package='pisces.io.lib',
    ext_modules=[Extension('libecompression', ['pisces/io/src/e_compression/e_compression.c']),
                 Extension('libconvert',glob.glob('pisces/io/src/convert/*.c'))],
    entry_points = """
        [console_scripts]
        pisces=pisces.commands.main:cli
        """,
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
