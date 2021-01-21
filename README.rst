APRS library for Python
~~~~~~~~~~~~~~~~~~~~~~~

|pypi| |coverage| |master_build| |docs|

A python library for dealing with APRS.
It can be used to interact with APRS-IS servers, sending and receiving.
Parsing functionally is also included, but currently doesn't implement the full spec.

See `the documentation <http://aprs-python.readthedocs.io/en/latest/>`_.

Installation
============

To install the latest release from ``pypi``::

    pip install aprslib

To install the latest dev version from the `Github repo <https://github.com/rossengeorgiev/aprs-python/>`_::

    pip install git+https://github.com/rossengeorgiev/aprs-python


Contribution
============

| Suggestions, issues and pull requests are welcome.
| Just visit the repository at https://github.com/rossengeorgiev/aprs-python


.. |pypi| image:: https://img.shields.io/pypi/v/aprslib.svg?style=flat&label=latest%20version
    :target: https://pypi.python.org/pypi/aprslib
    :alt: Latest version released on PyPi

.. |coverage| image:: https://img.shields.io/coveralls/rossengeorgiev/aprs-python/master.svg?style=flat
    :target: https://coveralls.io/r/rossengeorgiev/aprs-python?branch=master
    :alt: Test coverage

.. |master_build| image:: https://github.com/rossengeorgiev/aprs-python/workflows/Tests/badge.svg?branch=master
    :target: https://github.com/rossengeorgiev/aprs-python/actions?query=workflow%3A%22Tests%22+branch%3Amaster
    :alt: Build status of master branch

.. |docs| image:: https://readthedocs.org/projects/aprs-python/badge/?version=latest
    :target: http://aprs-python.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation status
