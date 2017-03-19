from aprslib.packets.base import APRSPacket

class TelemetryAddon(object):
    _analog_values = None
    _sequence_number = 0
    _digital_value = 0


    def __init__(self, *args, **kwargs):
        self._analog_values = AnalogList()
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

        self._analog_values[:] = v

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


class AnalogList(list):
    def __init__(self):
        list.__init__(self, [0] * 5)

    def __setitem__(self, i, v):
        if not 0 <= i <= 4:
            raise IndexError("Index outside of range 0-4, got %d" % i)
        if not 0 <= v <= 999:
            raise ValueError("Value outside of range 0-999, got %d" % v)
        else:
            list.__setitem__(self, i, v)

    def __setslice__(self, i, j, v):
        if i > j:
            i, j = j, i

        for x in range(max(0, i), min(5, j)):
            list.__setitem__(self, x, v[x])

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


class TelemetryReport(TelemetryAddon, APRSPacket):
    @property
    def format(self):
        return 'telemetry'

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
