# aprslib - Python library for working with APRS
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
Provides facilities for covertion from/to base91
"""

__all__ = ['to_decimal', 'from_decimal']
from math import log
from re import findall


def to_decimal(text):
    """
    Takes a base91 char string and returns decimal
    """

    if not isinstance(text, basestring):
        raise TypeError("expected str or unicode, %s given" % type(text))

    if findall(r"[\x00-\x20\x7c-\xff]", text):
        raise ValueError("invalid character in sequence")

    decimal = 0
    length = len(text) - 1
    for i, char in enumerate(text):
        decimal += (ord(char) - 33) * (91 ** (length - i))

    return decimal if text != '' else 0


def from_decimal(number, padding=1):
    """
    Takes a decimal and returns base91 char string.
    With optional padding to a specific length.
    """
    text = []

    if not isinstance(number, (int, long)) is not int or number < 0:
        raise ValueError("non-positive integer error")
    elif not isinstance(number, (int, long)) or padding < 1:
        raise ValueError("padding must be integer and >0")
    elif number > 0:
        for divisor in [91**e for e in reversed(range(int(log(number) / log(91)) + 1))]:
            quotient = number / divisor
            number = number % divisor
            text.append(chr(33 + quotient))

    # add padding if necessary
    text = ['!'] * (padding-len(text)) + text

    return "".join(text)
