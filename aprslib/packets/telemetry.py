from aprslib.packets.base import APRSPacket

class TelemetryReport(APRSPacket):
    format = 'raw'
    sequenceno = 0
    analog1 = 0
    analog2 = 0
    analog3 = 0
    analog4 = 0
    analog5 = 0
    digitalvalue = ['0']*8
    comment = ''

    def _serialize_body(self):
        # What do we do when len(digitalvalue) != 8?
        self.digitalvalue = ''.join(self.digitalvalue)

        body = [
            'T#',  # packet type
            str(self.sequenceno).zfill(3),
            str(self.analog1).zfill(3),
            str(self.analog2).zfill(3),
            str(self.analog3).zfill(3),
            str(self.analog4).zfill(3),
            str(self.analog5).zfill(3),
            str(self.digitalvalue),
            self.comment,
        ]
        tmpbody = ",".join(body)

        # remove static but erroneous comma between T# and sequenceno
        return tmpbody[:2] + tmpbody[3:]
