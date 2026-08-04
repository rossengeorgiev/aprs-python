from aprslib.exceptions import UnknownFormat
from aprslib.exceptions import ParseError

__all__ = [
        'parse_thirdparty',
        ]

def parse_thirdparty(body):
    parsed = {'format':'thirdparty'}

    # Import parse here to avoid circular import
    # (aprslib.parsing.__init__ imports us, we need its parse function)
    from aprslib.parsing import parse

    # Parse sub-packet
    try:
        subpacket = parse(body)
    except (UnknownFormat,ParseError):
        raise

    parsed.update({'subpacket':subpacket})

    return('',parsed)
