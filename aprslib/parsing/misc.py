import re
from aprslib.exceptions import ParseError
from aprslib.parsing.common import _parse_timestamp

__all__ = [
        '_parse_status',
        '_parse_invalid',
        '_parse_user_defined',
        ]


# STATUS PACKET
#
# >DDHHMMzComments
# >Comments
def _parse_status(packet_type, body):
    body, result = _parse_timestamp(body, packet_type)

    result.update({
        'format': 'status',
        'status': body.strip(' ')
        })

    return (body, result)


# INVALID
#
# ,.........................
def _parse_invalid(body):
    return ('', {
        'format': 'invalid',
        'body': body
        })


# USER DEFINED
#
# {A1................
# {{.................
def _parse_user_defined(body):
    return ('', {
        'format': 'user-defined',
        'id': body[0],
        'type': body[1],
        'body': body[2:],
        })
