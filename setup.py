#!/usr/bin/env python

from setuptools import setup, find_packages
from codecs import open
from os import path

from aprslib import __version__ as lib_version

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()\
                        .replace('.io/en/latest/', '.io/en/stable/')\
                        .replace('?badge=latest', '?badge=stable')\
                        .replace('projects/aprs-python/badge/?version=latest', 'projects/aprs-python/badge/?version=stable')

setup(
    name='aprslib',
    version=lib_version,
    description='Module for accessing APRS-IS and parsing APRS packets',
    long_description=long_description,
    url='https://github.com/rossengeorgiev/aprs-python',
    author='Rossen Georgiev',
    author_email='hello@rgp.io',
    license='GPLv2',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Communications :: Ham Radio',
    ],
    test_suite='tests',
    keywords='aprs aprslib parse parsing aprs-is library base91',
    packages=['aprslib'] + ['aprslib.'+x for x in find_packages(where='aprslib')],
    install_requires=[],
    zip_safe=True,
)
