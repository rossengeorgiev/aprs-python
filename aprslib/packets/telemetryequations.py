from aprslib.packets.base import APRSPacket

class TelemetryEquationsReport(APRSPacket):
    format = 'raw'
    telemetrystation = "N0CALL"
    a1a = "0.0"
    a1b = "1.0"
    a1c = "0.0"
    a2a = "0.0"
    a2b = "1.0"
    a2c = "0.0"
    a3a = "0.0"
    a3b = "1.0"
    a3c = "0.0"
    a4a = "0.0"
    a4b = "1.0"
    a4c = "0.0"
    a5a = "0.0"
    a5b = "1.0"
    a5c = "0.0"

    def _serialize_body(self):

        body = [
            ':{0} :EQNS.'.format(self.telemetrystation),  # packet type
            self.a1a,
            self.a1b,
            self.a1c,
            self.a2a,
            self.a2b,
            self.a2c,
            self.a3a,
            self.a3b,
            self.a3c,
            self.a4a,
            self.a4b,
            self.a4c,
            self.a5a,
            self.a5b,
            self.a5c,
        ]
        tmpbody = ",".join(body)
        badcomma = tmpbody.index(",")

        # remove static but erroneous comma between EQNS. and a1 value
        # Position can vary due to callsign
        return tmpbody[:badcomma] + tmpbody[badcomma+1:]
