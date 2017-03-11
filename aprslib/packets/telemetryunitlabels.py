from aprslib.packets.base import APRSPacket

class TelemetryUnitLabelsReport(APRSPacket):
    format = 'raw'
    telemetrystation = "N0CALL"
    a1 = "BITS"
    a2 = "BITS"
    a3 = "BITS"
    a4 = "BITS"
    a5 = "BITS"
    b1 = "EN"
    b2 = "EN"
    b3 = "EN"
    b4 = "EN"
    b5 = "EN"
    b6 = "EN"
    b7 = "EN"
    b8 = "EN"
    comment = ''

    def _serialize_body(self):

        body = [
            ':{0} :UNIT.'.format(self.telemetrystation),  # packet type
            self.a1,
            self.a2,
            self.a3,
            self.a4,
            self.a5,
            self.b1,
            self.b2,
            self.b3,
            self.b4,
            self.b5,
            self.b6,
            self.b7,
            self.b8,
        ]
        tmpbody = ",".join(body)
        badcomma = tmpbody.index(",")

        # remove static but erroneous comma between UNIT. and a1 value
        return tmpbody[:badcomma] + tmpbody[badcomma+1:]
