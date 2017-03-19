from aprslib import string_type
from aprslib.packets.base import APRSPacket

__all__ = [
    'TelemetryReport',
    'TelemetryUnit',
    'TelemetryParm',
]

class TelemetryAddon(object):
    _analog_values = None
    _sequence_number = 0
    _digital_value = 0

    def __init__(self, *args, **kwargs):
        self._analog_values = AnalogValueList()
        super(TelemetryAddon, self).__init__( *args, **kwargs)

    @property
    def analog_values(self):
        return self._analog_values

    @analog_values.setter
    def analog_values(self, v):
        if not isinstance(v, list):
            raise TypeError("Expected analog_values to be list, got %s" % type(v))
        if len(v) != 5:
            raise ValueError("Expected a list of 5 elements, got a list of %d" % len(v))

        for i, elm in enumerate(v):
            self._analog_values[i] = elm

    @property
    def sequence_number(self):
        return self._sequence_number

    @sequence_number.setter
    def sequence_number(self, v):
        if 0 <= v <= 999:
            self._sequence_number = v
        else:
            raise ValueError("Value outside of range 0-999")

    @property
    def digital_value(self):
        return self._digital_value

    @digital_value.setter
    def digital_value(self, v):
        if 0 <= v <= 0xFF:
            self._digital_value = v
        else:
            raise ValueError("Value outside of range 0-255")


class ImmutableList(list):
    def __setitem__(self, a, b):
        raise NotImplementedError("not supported")

    def __setslice__(self, a, b, c):
        raise NotImplementedError("not supported")

    def append(self, a):
        raise NotImplementedError("not supported")

    def remove(self, a):
        raise NotImplementedError("not supported")

    def pop(self, a):
        raise NotImplementedError("not supported")

    def extend(self, a):
        raise NotImplementedError("not supported")

    def insert(self, a, b):
        raise NotImplementedError("not supported")


class AnalogValueList(ImmutableList):
    def __init__(self):
        list.__init__(self, [0] * 5)

    def __setitem__(self, i, v):
        if not 0 <= i <= 4:
            raise IndexError("Index outside of range 0-4, got %d" % i)
        if not isinstance(v, int) or not 0 <= v <= 999:
            raise ValueError("Value outside of range 0-999, got %d" % v)

        list.__setitem__(self, i, v)


class UnitParmList(ImmutableList):
    _lengths = (7, 7, 6, 6, 5, 6, 5, 4, 4, 4, 3, 3, 3)

    def __init__(self):
        list.__init__(self, [''] * 13)

    def __setitem__(self, i, v):
        if not 0 <= i <= 12:
            raise IndexError("Index outside of range 0-12, got %d" % i)
        if not isinstance(v, string_type):
            raise TypeError("Expected type to be str, got %s" % type(v))
        if len(v) > self._lengths[i]:
            raise ValueError("Expected length index %d is %d, got %d" % (i, self._lengths[i], len(v)))

        list.__setitem__(self, i, v)


class TelemetryReport(TelemetryAddon, APRSPacket):
    format = 'telemetry'
    _comment = ''

    @property
    def comment(self):
        return self._comment

    @comment.setter
    def comment(self, v):
        if isinstance(v, str):
            self._comment = v
        else:
            raise TypeError("Expected comment to be of type str, got %s" % type(v))

    def _serialize_body(self):
        return ("T#" + ("{:03d}," * 6) + "{:08b}{:s}").format(
            self.sequence_number,
            self.analog_values[0],
            self.analog_values[1],
            self.analog_values[2],
            self.analog_values[3],
            self.analog_values[4],
            self.digital_value,
            self.comment,
            )

class TelemetryMessage(APRSPacket):
    format = 'telemetry-messsage'
    addressee = 'N0CALL'

    def _serialize_body(self):
        return ":{: <9s}:".format(self.addressee)

class TelemetryUnit(TelemetryMessage):
    _tUNIT = None

    def __init__(self, *args, **kwargs):
        self._tUNIT = UnitParmList()
        super(TelemetryUnit, self).__init__( *args, **kwargs)

    @property
    def tUNIT(self):
        return self._tUNIT

    @tUNIT.setter
    def tUNIT(self, v):
        if not isinstance(v, list):
            raise TypeError("Expected analog_values to be list, got %s" % type(v))
        if len(v) != 13:
            raise ValueError("Expected a list of 13 elements, got a list of %d" % len(v))

        for i, elm in enumerate(v):
            self._tUNIT[i] = elm

    def _serialize_body(self):
        last = 0
        for i, elm in enumerate(self.tUNIT):
            if elm: last = i

        return "{:s}{:s}{:s}".format(
            TelemetryMessage._serialize_body(self),
            'UNIT.',
            ','.join(self.tUNIT[:last+1]),
            )


class TelemetryParm(TelemetryMessage):
    _tPARM = None

    def __init__(self, *args, **kwargs):
        self._tPARM = UnitParmList()
        super(TelemetryParm, self).__init__( *args, **kwargs)

    @property
    def tPARM(self):
        return self._tPARM

    @tPARM.setter
    def tPARM(self, v):
        if not isinstance(v, list):
            raise TypeError("Expected analog_values to be list, got %s" % type(v))
        if len(v) != 13:
            raise ValueError("Expected a list of 13 elements, got a list of %d" % len(v))

        for i, elm in enumerate(v):
            self._tPARM[i] = elm

    def _serialize_body(self):
        last = 0
        for i, elm in enumerate(self.tPARM):
            if elm: last = i

        return "{:s}{:s}{:s}".format(
            TelemetryMessage._serialize_body(self),
            'PARM.',
            ','.join(self.tPARM[:last+1]),
            )
