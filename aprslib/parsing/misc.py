import re
from aprslib.exceptions import ParseError
from aprslib.parsing.common import _parse_timestamp

__all__ = [
        '_parse_status',
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
