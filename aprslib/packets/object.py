"""
APRS Object and Item packet construction.

Object format:
    ;name_____*DDHHMMzDDMM.MMN/DDDMM.MMWsymbol comment
    ;name_____*DDHHMMzDDMM.MMN/DDDMM.MMWsymbol comment  (live object, * = live)
    ;name_____*_DDHHMMzDDMM.MMN/DDDMM.MMWsymbol comment (killed object, _ = killed)

Item format:
    )name!DDMM.MMN/DDDMM.MMWsymbol comment  (live)
    )name_DDMM.MMN/DDDMM.MMWsymbol comment  (killed)

References:
    - APRS101 Chapter 11: Object and Item Reports
"""
from datetime import datetime, timezone
from aprslib.packets.base import APRSPacket
from aprslib.util import latitude_to_ddm, longitude_to_ddm, comment_altitude


class ObjectReport(APRSPacket):
    """
    APRS Object Report packet construction.

    Object names are padded to exactly 9 characters with spaces.
    """
    format = 'object'

    _latitude = 0
    @property
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, val):
        if -90 <= val <= 90:
            self._latitude = val
        else:
            raise ValueError("Latitude outside of -90 to 90 degree range")

    _longitude = 0
    @property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, val):
        if -180 <= val <= 180:
            self._longitude = val
        else:
            raise ValueError("Longitude outside of -180 to 180 degree range")

    name = ''
    alive = True  # True = live object, False = killed
    symbol_table = '/'
    symbol = 'l'
    altitude = None
    timestamp = None
    comment = ''

    def _serialize_body(self):
        # Object name: must be 1-9 printable ASCII characters, padded to 9
        if (not isinstance(self.name, str) or not self.name
                or len(self.name) > 9
                or not self.name.isascii() or not self.name.isprintable()):
            raise ValueError("Object name must be 1-9 printable ASCII characters")
        obj_name = self.name.ljust(9)

        # Live/killed marker
        marker = '*' if self.alive else '_'

        # Timestamp
        if self.timestamp is None:
            ts = datetime.now(timezone.utc).strftime("%d%H%M") + 'z'
        elif isinstance(self.timestamp, str):
            ts = self.timestamp
        else:
            ts = datetime.fromtimestamp(self.timestamp, tz=timezone.utc).strftime("%d%H%M") + 'z'

        body = [
            ';',
            obj_name,
            marker,
            ts,
            latitude_to_ddm(self.latitude),
            self.symbol_table,
            longitude_to_ddm(self.longitude),
            self.symbol,
            comment_altitude(self.altitude) if self.altitude is not None else '',
            self.comment,
        ]

        return "".join(body)


class ItemReport(APRSPacket):
    """
    APRS Item Report packet construction.

    Item names are 3-9 characters (no padding).
    """
    format = 'item'

    _latitude = 0
    @property
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, val):
        if -90 <= val <= 90:
            self._latitude = val
        else:
            raise ValueError("Latitude outside of -90 to 90 degree range")

    _longitude = 0
    @property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, val):
        if -180 <= val <= 180:
            self._longitude = val
        else:
            raise ValueError("Longitude outside of -180 to 180 degree range")

    name = ''
    alive = True  # True = live item, False = killed
    symbol_table = '/'
    symbol = 'l'
    altitude = None
    comment = ''

    def _serialize_body(self):
        # Item name: must be 3-9 printable ASCII characters, not padded
        if (not isinstance(self.name, str)
                or not 3 <= len(self.name) <= 9
                or not self.name.isascii() or not self.name.isprintable()):
            raise ValueError("Item name must be 3-9 printable ASCII characters")
        item_name = self.name

        # Live/killed marker: ! = live, _ = killed
        marker = '!' if self.alive else '_'

        body = [
            ')',
            item_name,
            marker,
            latitude_to_ddm(self.latitude),
            self.symbol_table,
            longitude_to_ddm(self.longitude),
            self.symbol,
            comment_altitude(self.altitude) if self.altitude is not None else '',
            self.comment,
        ]

        return "".join(body)
