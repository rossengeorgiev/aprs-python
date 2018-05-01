
import unittest2 as unittest

from aprslib import parse
from aprslib.exceptions import ParseError, UnknownFormat


class thirdpartyTC(unittest.TestCase):
    def test_empty_subpacket(self):
        self.assertRaises(ParseError, parse, "A>B:}")

    def test_no_body(self):
        self.assertRaises(ParseError, parse, "A>B:}C>D")

    def test_empty_body(self):
        self.assertRaises(ParseError, parse, "A>B:}C>D:")

    def testparse_header_exception(self):
        self.assertRaises(ParseError, parse, "A>B:}C:asd")

    def test_empty_body_of_format_that_is_not_status(self):
        self.assertRaises(ParseError, parse, "A>B:}C>D:!")

        try:
            parse("A>B:}C>D:>")
        except:
            self.fail("empty status packet shouldn't raise exception")

    def test_unsupported_formats_raising(self):
        with self.assertRaises(UnknownFormat):
            for packet_type in '#$%)*,<?T[_{':
                packet = "A>B:}C>D:%saaa" % packet_type

                try:
                    parse(packet)
                except UnknownFormat as exp:
                    self.assertEqual(exp.packet, packet)
                    raise

    def test_valid_thirdparty_msg(self):
        packet = "A-1>APRS,B-2,WIDE1*:}C>APU25N,TCPIP,A-1*::DEF      :ack56"
        result = parse(packet)
        self.assertEqual(result['via'],'')
        self.assertEqual(result['to'],'APRS')
        self.assertEqual(result['from'],'A-1')
        self.assertEqual(result['format'],'thirdparty')
        self.assertEqual(result['raw'],packet)
        self.assertEqual(result['path'],['B-2', 'WIDE1*'])
        self.assertEqual(result['subpacket']['raw'],packet[21:])
        self.assertEqual(result['subpacket']['via'],'')
        self.assertEqual(result['subpacket']['msgNo'],'56')
        self.assertEqual(result['subpacket']['from'],'C')
        self.assertEqual(result['subpacket']['path'],['TCPIP', 'A-1*'])
        self.assertEqual(result['subpacket']['response'],'ack')
        self.assertEqual(result['subpacket']['format'],'message')
        self.assertEqual(result['subpacket']['to'],'APU25N')
        self.assertEqual(result['subpacket']['addresse'],'DEF')

