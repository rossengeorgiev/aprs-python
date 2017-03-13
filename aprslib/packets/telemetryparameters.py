from aprslib.packets.base import APRSPacket

class TelemetryParametersReport(APRSPacket):
    format = 'raw'
    telemetrystation = "N0CALL"
    a1 = "AN1"
    a2 = "AN2"
    a3 = "AN3"
    a4 = "AN4"
    a5 = "AN5"
    b1 = "D1"
    b2 = "D2"
    b3 = "D3"
    b4 = "D4"
    b5 = "D5"
    b6 = "D6"
    b7 = "D7"
    b8 = "D8"

    def _serialize_body(self):

        body = [
            ':{0} :PARM.'.format(self.telemetrystation),  # packet type
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

        # remove static but erroneous comma between PARM. and a1 value
        # Position can vary due to callsign
        return tmpbody[:badcomma] + tmpbody[badcomma+1:]
