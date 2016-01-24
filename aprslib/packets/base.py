

class APRSPacket(object):
    def __init__(self, fromcall, tocall, path=[]):
        self.fromcall = fromcall
        self.tocall = tocall
        self.path = path

    def __repr__(self):
        return "<%s(%s)>" % (
                    self.__class__.__name__,
                    repr(str(self)),
                    )

    def _serialize_header(self):
        header = "%s>%s" % (self.fromcall, self.tocall)

        if self.path:
            header += "," + ",".join(self.path)

        return header

    def _serialize_body(self):
        return getattr(self, 'body', '')

    def __str__(self):
        return "%s:%s" % (
            self._serialize_header(),
            self._serialize_body(),
            )

