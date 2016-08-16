aprslib documentation
*********************

|pypi| |coverage|

A python library for dealing with APRS.
It can be used to interact with APRS-IS servers, sending and receiving.
Parsing functionally is also included, but currently doesn't implement the full spec.
See the section for :ref:`supported formats<sup_formats>`.


Installation
============

To install the latest release from ``pypi``::

    pip install aprslib

To install the latest dev version from the `Github repo <https://github.com/rossengeorgiev/aprs-python/>`_::

    pip install git+https://github.com/rossengeorgiev/aprs-python

Contents
========

| Version: |version|
| Generated on: |today|

.. toctree::
   :maxdepth: 3

   examples
   parse_formats


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. |pypi| image:: https://img.shields.io/pypi/v/aprslib.svg?style=flat&label=pypi%20version
    :target: https://pypi.python.org/pypi/aprslib
    :alt: Latest version released on PyPi

.. |coverage| image:: https://img.shields.io/coveralls/rossengeorgiev/aprs-python/master.svg?style=flat
    :target: https://coveralls.io/r/rossengeorgiev/aprs-python?branch=master
    :alt: Test coverage
