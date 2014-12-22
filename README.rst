APRS lib for Python
~~~~~~~~~~~~~~~~~~~

|Build Status| |Coverage Status|

A tiny library for dealing with APRS. It can be used to connect and listen to the aprs-is feed as well as parse packets.
The following packet formats are supported:

-  normal/compressed position reports
-  mic-e
-  messages (inc. telemetry, bulletins, etc)
-  base91 comment telemetry

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

APRS-IS
^^^^^^^

.. code:: python

    import aprslib

    def callback(packet):
        print packet

    AIS = aprslib.IS("LZ1DEV")
    AIS.connect()
    # by default `raw` is False, then each line is ran through aprslib.parse()
    AIS.consumer(callback, raw=True)

.. code:: text

    VK2TRL>APU25N,qAR,VK3KAW:;AWARC    *270052z3602.24S/14656.26E-Albury/Wodonga A.R.C. see www.awarc.org
    DL1TMF-1>APRS,TCPIP*,qAS,DL1TMF:!5022.38N/01146.58E- http://www.dl1tmf.de
    KF4HFE-1>S3SX9S,K4TQR-1,WIDE1,AB4KN-2*,WIDE2,qAR,W4GR-10:`r,^l\Lk/"5h}
    ON0WTO-2>APNU19-3,WIDE,qAR,ON4AVM-11:!5037.46NL00423.37E# UIDIGI 1.9 B3 W3 NEW Paradigm sysop ON5YN
    PD2RLD-12>APJI41,TCPIP*,qAC,PD2RLD-JS:!5314.20NI00542.26E&- Roland - Bitgummole - www.PD2RLD.nl -
    N3BJY-C>APDG02,TCPIP*,qAC,N3BJY-CS:!4027.00ND08018.00W&RNG0000 2m Voice 146.49375MHz +0.0000MHz
    DO9ST-10>AP4R10,TCPIP*,qAC,T2LEIPZIG:!4900.24N/00940.81E&PHG4240 APRS4R IGATE
    ...

Docs
^^^^

.. code:: bash

    $ python -m pydoc aprslib

.. |Build Status| image:: https://travis-ci.org/rossengeorgiev/aprs-python.svg?branch=master
   :target: https://travis-ci.org/rossengeorgiev/aprs-python
.. |Coverage Status| image:: https://coveralls.io/repos/rossengeorgiev/aprs-python/badge.png?branch=master
   :target: https://coveralls.io/r/rossengeorgiev/aprs-python?branch=master


