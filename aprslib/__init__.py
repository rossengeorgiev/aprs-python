# aprs - Python library for dealing with APRS
# Copyright (C) 2013-2014 Rossen Georgiev
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
APRS library in Python

Currently the library provides facilities to:
    - parse APRS packets
    - Connect and listen to an aprs-is packet feed
"""

from datetime import date as _date
__date__ = str(_date.today())
del _date

from .version import __version__ as ref_version
__version__ = ref_version
del ref_version

__author__ = "Rossen Georgiev"
__all__ = ['IS', 'parse']

from .parse import parse as refparse
parse = refparse
del refparse

from .IS import IS as refIS


class IS(refIS):
    pass

del refIS
