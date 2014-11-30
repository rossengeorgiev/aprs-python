"""
Provides facilities for covertion from/to base91
"""
from math import log
from re import findall

def to_decimal(text):
    """
    Takes a base91 char string and returns decimal
    """

    if not isinstance(text, str):
        raise TypeError("expected str")

    if findall(r"[\x00-\x20\x7c-\xff]", text):
        raise ValueError("invalid character in sequence")

    decimal = 0
    length = len(text) - 1
    for i, char in enumerate(text):
        decimal += (ord(char) - 33) * (91 ** (length - i))

    return decimal if text != '' else 0


def from_decimal(n, padding=1):
    """
    Takes a decimal and returns base91 char string.
    With optional padding to a specific length.
    """
    text = []

    if not isinstance(n, (int, long)) is not int or n < 0:
        raise ValueError("non-positive integer error")
    elif not isinstance(n, (int, long)) or padding < 1:
        raise ValueError("padding must be integer and >0")
    elif n > 0:
        for d in [91**e for e in reversed(range(int(log(n) / log(91)) + 1))]:
            q = n / d
            n = n % d
            text.append(chr(33 + q))

    # add padding if necessary
    text = ['!'] * (padding-len(text)) + text

    return "".join(text)
