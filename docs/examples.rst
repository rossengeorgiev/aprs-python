Example usage
*************

This section includes examples of basic usage


Parsing a packet
================

.. code:: python

    >>> import aprslib
    >>> aprslib.parse("M0XER-4>APRS64,TF3RPF,WIDE2*,qAR,TF3SUT-2:!/.(M4I^C,O `DXa/A=040849|#B>@\"v90!+|")

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

.. note::
    Keep in mind that this function raises exceptions
    if the packet format is invalid or not supported.

.. code:: python

    try:
        packet = aprslib.parse("M0XER-4>APRS64,TF3RPF,WIDE2*,qAR,TF3SUT-2:!/.(M4I^C,O `DXa/A=040849|#B>@\"v90!+|")
    except (aprslib.ParseError, aprslib.UnknownFormat) as exp:
        pass


APRS-IS
=======

Connect to a feed
-----------------

Connecting to APRS-IS is done using the :py:class:`aprslib.IS` module.

.. code:: python

    import aprslib

    def callback(packet):
        print packet

    AIS = aprslib.IS("N0CALL")
    AIS.connect()
    # by default `raw` is False, then each line is ran through aprslib.parse()
    AIS.consumer(callback, raw=True)

Program output:

.. code:: text

    VK2TRL>APU25N,qAR,VK3KAW:;AWARC    *270052z3602.24S/14656.26E-Albury/Wodonga A.R.C. see www.awarc.org
    DL1TMF-1>APRS,TCPIP*,qAS,DL1TMF:!5022.38N/01146.58E- http://www.dl1tmf.de
    KF4HFE-1>S3SX9S,K4TQR-1,WIDE1,AB4KN-2*,WIDE2,qAR,W4GR-10:`r,^l\Lk/"5h}
    ...


Logging
-------

The :py:class:`aprslib.IS` module makes use of the ``logging`` module.
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

Program output:

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


Sending a packet
----------------

Uploading packets to APRS-IS is possible through the ``sendall()`` method in ``IS``.
The method assumes a single line/packet per call. The parameters may end with ``\r\n``, but it's not required.

.. code:: python

    import aprslib

    # a valid passcode for the callsign is required in order to send
    AIS = aprslib.IS("N0CALL", passwd="123456", port=14580)
    AIS.connect()
    # send a single status message
    AIS.sendall("N0CALL>APRS,TCPIP*:>status text")

Passcodes
---------

In order for the server to accept your packets, you need to send a valid passcode.
See :py:func:`aprslib.passcode`
