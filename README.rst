APRS library for Python
~~~~~~~~~~~~~~~~~~~~~~~

|Build Status| |Coverage Status|

A tiny library for dealing with APRS. It can be used to connect and listen to the APRS-IS feed as well as upload.
Parsing of packets is also possible, but the entire spec is not fully implemented yet.
The following is supported:

-  normal/compressed position reports
-  objects
-  mic-e position report
-  messages (inc. telemetry, bulletins, etc)
-  base91 comment telemetry extension
-  altitude extension
-  beacons

Packets can often contain characters outside of 7-bit ASCII.
``aprslib.parse()`` will attempt to guess the charset and return ``unicode`` strings using these steps and in that order:

1. Attempt to decode string as ``utf-8``
2. Attempt to guess the charset using ``chardet`` module (if installed), decode if confidence factor is sufficient
3. Finally, decode as ``latin-1``

Install
-----------

You can grab the latest release from https://pypi.python.org/pypi/aprslib or via ``pip``

.. code:: bash

    pip install aprslib

Examples
-----------

Parsing
^^^^^^^

.. code:: python

    import aprslib
    packet = aprslib.parse("M0XER-4>APRS64,TF3RPF,WIDE2*,qAR,TF3SUT-2:!/.(M4I^C,O `DXa/A=040849|#B>@\"v90!+|")

.. code:: python

    {'altitude': 12450.7752,
     'comment': 'Xa',
     'format': 'compressed',
     'from': 'M0XER-4',
     'gpsfixstatus': 1,
     'latitude': 64.11987367625208,
     'longitude': -19.070654142799384,
     'messagecapable': False,
     'path': ['TF3RPF', 'WIDE2*', 'qAR', 'TF3SUT-2'],
     'raw': 'M0XER-4>APRS64,TF3RPF,WIDE2*,qAR,TF3SUT-2:!/.(M4I^C,O `DXa/A=040849|#B>@"v90!+|',
     'symbol': 'O',
     'symbol_table': '/',
     'telemetry': {'bits': '00000000',
                   'seq': 215,
                   'vals': [2670, 176, 2199, 10, 0]},
     'to': 'APRS64',
     'via': 'TF3SUT-2'}

Keep in mind that this function raises exceptions if the packet format is invalid or not supported.

.. code:: python

    try:
        packet = aprslib.parse("M0XER-4>APRS64,TF3RPF,WIDE2*,qAR,TF3SUT-2:!/.(M4I^C,O `DXa/A=040849|#B>@\"v90!+|")
    except (aprslib.ParseError, aprslib.UnknownFormat) as exp:
        pass


APRS-IS
^^^^^^^

.. code:: python

    import aprslib

    def callback(packet):
        print packet

    AIS = aprslib.IS("N0CALL")
    AIS.connect()
    # by default `raw` is False, then each line is ran through aprslib.parse()
    AIS.consumer(callback, raw=True)

.. code:: text

    VK2TRL>APU25N,qAR,VK3KAW:;AWARC    *270052z3602.24S/14656.26E-Albury/Wodonga A.R.C. see www.awarc.org
    DL1TMF-1>APRS,TCPIP*,qAS,DL1TMF:!5022.38N/01146.58E- http://www.dl1tmf.de
    KF4HFE-1>S3SX9S,K4TQR-1,WIDE1,AB4KN-2*,WIDE2,qAR,W4GR-10:`r,^l\Lk/"5h}
    ...

The ``IS`` class makes use of the ``logging`` module.
There are various levels of verbosity available for ``IS``.
The only non-standard levels are 9 (unknown format errors) and 11 (parse errors).
Here is a simple example:

.. code:: python

    import aprslib
    import logging

    logging.basicConfig(level=logging.DEBUG) # level=10

    AIS = aprslib.IS("N0CALL")
    AIS.connect()
    AIS.consumer(lambda x: None, raw=True)

.. code:: text

    INFO:aprslib.IS:Attempting connection to rotate.aprs.net:10152
    INFO:aprslib.IS:Connected to 205.233.35.52:10152
    DEBUG:aprslib.IS:Banner: # aprsc 2.0.14-g28c5a6a
    INFO:aprslib.IS:Sending login information
    DEBUG:aprslib.IS:Server: # logresp N0CALL unverified, server EIGHTH
    INFO:aprslib.IS:Login successful (receive only)
    DEBUG:aprslib.parse:Parsing: PY4MM-15>Q8U11W,PU4YRM-15*,WIDE3-2,qAR,PP2MD-1:'L.Kl #/"=h}APRS DIGI - Uberlandia - MG
    DEBUG:aprslib.parse:Attempting to parse as mic-e packet
    DEBUG:aprslib.parse:Parsed ok.
    ...

Uploading packets to APRS-IS is possible through the ``sendall()`` method in ``IS``.
The method assumes a single line/packet per call. The parameters may end with ``\r\n``, but it's not required.

.. code:: python

    import aprslib

    # a valid passcode for the callsign is required in order to send
    AIS = aprslib.IS("N0CALL", passcode="123456", port=14580)
    AIS.connect()
    # send a single status message
    AIS.sendall("N0CALL>APRS,TCPIP*:>status text")

A passcode generation function is also provided.

CHANGES
^^^^^^^

You can find the latest changes between versions in the CHANGES file.

Docs
^^^^

.. code:: bash

    $ python -m pydoc aprslib

.. |Build Status| image:: https://travis-ci.org/rossengeorgiev/aprs-python.svg?branch=master
   :target: https://travis-ci.org/rossengeorgiev/aprs-python
.. |Coverage Status| image:: https://coveralls.io/repos/rossengeorgiev/aprs-python/badge.png?branch=master
   :target: https://coveralls.io/r/rossengeorgiev/aprs-python?branch=master


