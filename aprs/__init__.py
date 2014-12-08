
"""
APRS library in Python

Currently the library provides facilities to:
    - parse APRS packets
    - Connect and listen to an aprs-is packet feed

Copyright 2013-2014 (C), Rossen Georgiev
"""

from datetime import date as _date
__date__ = str(_date.today())
del _date

from . import version
__version__ = version.__version__
del version

__author__ = "Rossen Georgiev"

from .IS import IS
from .parse import parse

__all__ = ['IS', 'parse']
