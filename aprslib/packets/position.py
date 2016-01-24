from datetime import datetime
from aprslib.packets.base import APRSPacket
from aprslib.util import latitude_to_ddm, longitude_to_ddm, comment_altitude


class PositionReport(APRSPacket):
    format = 'uncompressed'
    latitude = 0
    longitude = 0
    symbol_table = '/'
    symbol = 'l'
    altitude = None
    timestamp = None
    comment = ''

    def _serialize_body(self):

        if self.timestamp is None:
            timestamp = ''
        elif isinstance(self.timestamp, str):
            timestamp = self.timestamp
        else:
            timestamp = datetime.utcfromtimestamp(self.timestamp).strftime("%d%H%M") + 'z'

        body = [
            '/' if self.timestamp else '!',  # packet type
            timestamp,
            latitude_to_ddm(self.latitude),
            self.symbol_table,
            longitude_to_ddm(self.longitude),
            self.symbol,
            comment_altitude(self.altitude) if self.altitude is not None else '',
            self.comment,
        ]

        return "".join(body)



