#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" 
Pisces: A Practical Seismological Database Library in Python


"""
from setuptools import setup

# from numpy.distutils.core import setup, Extension

with open('README.md') as readme:
    # https://dustingram.com/articles/2018/03/16/markdown-descriptions-on-pypi
    long_description = readme.read()

doclines = __doc__.split("\n")

setup(name='pisces',
      version='0.4.0',
      description='A Practical Seismological Database Library in Python.',
      long_description=long_description,
      long_description_content_type="text/markdown", # setuptools >= 38.6.0
      author='Jonathan MacCarthy',
      author_email='jkmacc@lanl.gov',
      packages=['pisces','pisces.schema','pisces.io','pisces.tables',
                'pisces.commands'],
      url='https://github.com/LANL-Seismoacoustics/pisces',
      download_url='https://github.com/LANL-Seismoacoustics/pisces/tarball/0.3.2',
      keywords = ['seismology', 'geophysics', 'database'],
      install_requires=['numpy','obspy>=1.0','sqlalchemy>=1.4','Click'],
      extras_require={
         'e1': ["e1"],
      },
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
                   'Programming Language :: Python :: 3',
                   'Topic :: Scientific/Engineering',
                   'Topic :: Database',
                   'Topic :: Scientific/Engineering :: Physics'],
)
