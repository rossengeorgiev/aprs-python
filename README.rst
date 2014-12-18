APRS lib for Python
~~~~~~~~~~~~~~~~~~~

|Build Status| |Coverage Status|

| A tiny library for dealing with APRS. It can be used to connect and
listen to the aprs-is feed as well as parse packets.
| The following packet formats are supported:

-  normal/compressed position reports
-  mic-e
-  messages (inc. telemetry, bulletins, etc)
-  base91 commenet telemetry

Quick start
-----------

Parsing
^^^^^^^

.. code:: python

    import aprs
    packet = aprs.parse('LZ1DEV>APRS:>status text')

APRS-IS
^^^^^^^

.. code:: python

    import aprs

    def callback(packet):
        print packet

    AIS = aprs.IS("LZ1DEV")
    AIS.connect()
    AIS.consumer(callback) 

Docs
^^^^

.. code:: bash

    $ python -m pydoc aprs

.. |Build Status| image:: https://travis-ci.org/rossengeorgiev/aprs-python.svg?branch=master
   :target: https://travis-ci.org/rossengeorgiev/aprs-python
.. |Coverage Status| image:: https://coveralls.io/repos/rossengeorgiev/aprs-python/badge.png?branch=master
   :target: https://coveralls.io/r/rossengeorgiev/aprs-python?branch=master
