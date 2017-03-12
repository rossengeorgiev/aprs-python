from aprslib.packets.base import APRSPacket

class TelemetrySenseProjectReport(APRSPacket):
    format = 'raw'
    telemetrystation = "N0CALL"
    digitalvalue = ['0']*8
    project = ''

    def _serialize_body(self):
        # What do we do when len(digitalvalue) != 8?
        self.digitalvalue = ''.join(self.digitalvalue)

        body = [
            ':{0} :BITS.'.format(self.telemetrystation),  # packet type
            str(self.digitalvalue),
            self.project,
        ]
        tmpbody = ",".join(body)
        badcomma = tmpbody.index(",")

        # remove static but erroneous comma between BITS. and digitalvalue
        # Position can vary due to callsign
        return tmpbody[:badcomma] + tmpbody[badcomma + 1:]
