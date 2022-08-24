Packet parsing
**************

An overview of the parsing functionality.

APRS Reference
==============

The implementation follows the APRS Protocol Reference

* Version 1.0: http://www.aprs.org/doc/APRS101.PDF
* Version 1.1: http://www.aprs.org/aprs11.html
* Version 1.2: http://www.aprs.org/aprs12.html


Encodings
=========

Packets can often contain characters outside of 7-bit ASCII.
:py:func:`aprslib.parse` will attempt to guess the charset and return ``unicode`` strings using these steps and in that order:

1. Attempt to decode string as ``utf-8``
2. Attempt to guess the charset using ``chardet`` module (if installed), decode if confidence factor is sufficient
3. Finally, decode as ``latin-1``


.. _sup_formats:

Supported formats
=================

- normal/compressed position reports
- mic-e position reports
- objects reports
- weather reports
- status reports
- messages (inc. telemetry, bulletins, etc)
- base91 comment telemetry extension
- altitude extension
- beacons


Position reports
================

Normal
------

.. code:: python

    >>> aprslib.parse("FROMCALL>TOCALL:!4903.50N/07201.75W-Test /A=001234")

    {'altitude': 376.1232,
     'comment': u'Test',
     'format': 'uncompressed',
     'from': u'FROMCALL',
     'latitude': 49.05833333333333,
     'longitude': -72.02916666666667,
     'messagecapable': False,
     'path': [],
     'posambiguity': 0,
     'raw': u'FROMCALL>TOCALL:!4903.50N/07201.75W-Test /A=001234',
     'symbol': u'-',
     'symbol_table': u'/',
     'to': u'TOCALL',
     'via': ''}


Compressed
----------

.. code:: python

    >>> aprslib.parse("M0XER-4>APRS64,TF3RPF,WIDE2*,qAR,TF3SUT-2:!/.(M4I^C,O `DXa/A=040849|#B>@\"v90!+|")

    {'altitude': 12450.7752,
     'comment': u'Xa',
     'format': 'compressed',
     'from': u'M0XER-4',
     'gpsfixstatus': 1,
     'latitude': 64.11987367625208,
     'longitude': -19.070654142799384,
     'messagecapable': False,
     'path': [u'TF3RPF', u'WIDE2*', u'qAR', u'TF3SUT-2'],
     'raw': u'M0XER-4>APRS64,TF3RPF,WIDE2*,qAR,TF3SUT-2:!/.(M4I^C,O `DXa/A=040849|#B>@"v90!+|',
     'symbol': u'O',
     'symbol_table': u'/',
     'telemetry': {'bits': '00000000',
      'seq': 215,
      'vals': [2670, 176, 2199, 10, 0]},
     'to': u'APRS64',
     'via': u'TF3SUT-2'}

With timestamp:

.. code:: python

    >>> aprslib.parse("FROMCALL>TOCALL:/092345z4903.50N/07201.75W>Test1234")

    {'comment': u'Test1234',
     'format': 'uncompressed',
     'from': u'FROMCALL',
     'latitude': 49.05833333333333,
     'longitude': -72.02916666666667,
     'messagecapable': False,
     'path': [],
     'posambiguity': 0,
     'raw': u'FROMCALL>TOCALL:/092345z4903.50N/07201.75W>Test1234',
     'raw_timestamp': u'092345z',
     'symbol': u'>',
     'symbol_table': u'/',
     'timestamp': 1452383100,
     'to': u'TOCALL',
     'via': ''}

Mic-E
-----

.. code:: python

    >>> aprslib.parse('FROMCALL>SUSUR1:`CF"l#![/`"3z}_ ')

    {'altitude': 8,
     'comment': u'`_',
     'course': 305,
     'format': 'mic-e',
     'from': u'FROMCALL',
     'latitude': 35.58683333333333,
     'longitude': 139.701,
     'mbits': u'111',
     'mtype': 'M0: Off Duty',
     'path': [],
     'posambiguity': 0,
     'raw': u'FROMCALL>SUSUR1:`CF"l#![/`"3z}_ ',
     'speed': 0.0,
     'symbol': u'[',
     'symbol_table': u'/',
     'to': u'SUSUR1',
     'via': ''}

Objects
=======

.. code:: python

    >>> aprslib.parse('FROMCALL>TOCALL:;LEADER   *092345z4903.50N/07201.75W>088/036')

    {'alive': True,
     'comment': u'',
     'course': 88,
     'format': 'object',
     'from': u'FROMCALL',
     'latitude': 49.05833333333333,
     'longitude': -72.02916666666667,
     'object_format': 'uncompressed',
     'object_name': u'LEADER   ',
     'path': [],
     'posambiguity': 0,
     'raw': u'FROMCALL>TOCALL:;LEADER   *092345z4903.50N/07201.75W>088/036',
     'raw_timestamp': u'092345z',
     'speed': 66.672,
     'symbol': u'>',
     'symbol_table': u'/',
     'timestamp': 1452383100,
     'to': u'TOCALL',
     'via': ''}

Weather
=======

Positionless
------------

.. code:: python

    >>> aprslib.parse('FROMCALL>TOCALL:_10090556c220s004g005t077r000p000P000h50b09900wRSW')

    {'comment': u'wRSW',
     'format': 'wx',
     'from': u'FROMCALL',
     'path': [],
     'raw': u'FROMCALL>TOCALL:_10090556c220s004g005t077r000p000P000h50b09900wRSW',
     'to': u'TOCALL',
     'via': '',
     'weather': {'humidity': 50,
      'pressure': 990.0,
      'rain_1h': 0.0,
      'rain_24h': 0.0,
      'rain_since_midnight': 0.0,
      'temperature': 25.0,
      'wind_direction': 220,
      'wind_gust': 2.2352,
      'wind_speed': 1.78816},
     'wx_raw_timestamp': u'10090556'}

Comment field
-------------

.. code:: python

    >>> aprslib.parse("FROMCALL>TOCALL:=4903.50N/07201.75W_225/000g000t050r000p001...h00b10138dU2k")

    {'comment': u'...dU2k',
     'format': 'uncompressed',
     'from': u'FROMCALL',
     'latitude': 49.05833333333333,
     'longitude': -72.02916666666667,
     'messagecapable': True,
     'path': [],
     'posambiguity': 0,
     'raw': u'FROMCALL>TOCALL:=4903.50N/07201.75W_225/000g000t050r000p001...h00b10138dU2k',
     'symbol': u'_',
     'symbol_table': u'/',
     'to': u'TOCALL',
     'via': '',
     'weather': {'humidity': 0,
      'pressure': 1013.8,
      'rain_1h': 0.0,
      'rain_24h': 0.254,
      'temperature': 10.0,
      'wind_direction': 225,
      'wind_gust': 0.0,
      'wind_speed': 0.0}}

Status report
=============

.. code:: python

    >>> aprslib.parse('FROMCALL>TOCALL:>status text')

    {'format': 'status',
     'from': u'FROMCALL',
     'path': [],
     'raw': u'FROMCALL>TOCALL:>status text',
     'status': u'status text',
     'to': u'TOCALL',
     'via': ''}

Messages
========


Regular
-------

.. code:: python

    >>>  aprslib.parse('FROMCALL>TOCALL::ADDRCALL :message text')

    {'addresse': u'ADDRCALL',
     'format': 'message',
     'from': u'FROMCALL',
     'message_text': u'message text',
     'path': [],
     'raw': u'FROMCALL>TOCALL::FROMCALL :message text',
     'to': u'TOCALL',
     'via': ''}


Telemetry report
-----------------------


.. code:: python

    >>> aprslib.parse("FROMCALL>APDW16,WIDE1-1,qAR,TOCALL:T#165,13.21,0.39,5.10,14.94,36.12,11111100")

    {
    'raw': 'FROMCALL>APDW16,WIDE1-1,qAR,TOCALL:T#165,13.21,0.39,5.10,14.94,36.12,11111100',
    'from': 'FROMCALL',
    'to': 'APDW16',
    'path': ['WIDE1-1', 'qAR', 'TOCALL'],
    'via': 'TOCALL',
    'telemetry':
    {
        'seq': 165,
        'vals': [13.21, 0.39, 5.1, 14.94, 36.12],
        'bits': '11111100'
    },
    'format': 'beacon',
    'text': 'T#165,13.21,0.39,5.10,14.94,36.12,11111100'
    }


Telemetry configuration
-----------------------


.. code:: python

    >>> aprslib.parse('FROMCALL>TOCALL::FROMCALL :PARM.Vin,Rx1h,Dg1h,Eff1h,A5,O1,O2,O3,O4,I1,I2,I3,I4')

    {'addresse': 'FROMCALL',
     'format': 'telemetry-message',
     'from': 'FROMCALL',
     'path': [],
     'raw': 'FROMCALL>TOCALL::FROMCALL :PARM.Vin,Rx1h,Dg1h,Eff1h,A5,O1,O2,O3,O4,I1,I2,I3,I4',
     'tPARM': ['Vin', 'Rx1h', 'Dg1h', 'Eff1h', 'A5', 'O1', 'O2', 'O3', 'O4', 'I1', 'I2', 'I3', 'I4'],
     'to': 'TOCALL',
     'via': ''}

    >>> aprslib.parse('FROMCALL>TOCALL::FROMCALL :UNIT.Volt,Pkt,Pkt,Pcnt,None,On,On,On,On,Hi,Hi,Hi,Hi')

    {'addresse': 'FROMCALL',
     'format': 'telemetry-message',
     'from': 'FROMCALL',
     'path': [],
     'raw': 'FROMCALL>TOCALL::FROMCALL :UNIT.Volt,Pkt,Pkt,Pcnt,None,On,On,On,On,Hi,Hi,Hi,Hi',
     'tUNIT': ['Volt', 'Pkt', 'Pkt', 'Pcnt', 'None', 'On', 'On', 'On', 'On', 'Hi', 'Hi', 'Hi', 'Hi'],
     'to': 'TOCALL',
     'via': ''}

    >>> aprslib.parse('FROMCALL>TOCALL::FROMCALL :EQNS.0,0.075,0,0,10,0,0,10,0,0,1,0,0,0,0')

    {'addresse': 'FROMCALL',
     'format': 'telemetry-message',
     'from': 'FROMCALL',
     'path': [],
     'raw': 'FROMCALL>TOCALL::FROMCALL :EQNS.0,0.075,0,0,10,0,0,10,0,0,1,0,0,0,0',
     'tEQNS': [[0, 0.075, 0], [0, 10, 0], [0, 10, 0], [0, 1, 0], [0, 0, 0]],
     'to': 'TOCALL',
     'via': ''}



