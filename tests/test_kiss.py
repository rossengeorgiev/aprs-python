"""Tests for KISS <-> TNC-2 conversion."""
import unittest
from aprslib.kiss import kiss_to_tnc2, tnc2_to_kiss, _encode_ax25_call, _decode_ax25_call


class KissToTnc2Test(unittest.TestCase):
    """Test KISS frame to TNC-2 format conversion."""

    def test_simple_packet(self):
        """Test a basic KISS frame decodes to TNC-2."""
        # Build a known AX.25 frame: N0CALL>APRS:!4903.50N/07201.75W-
        tnc2 = "N0CALL>APRS:!4903.50N/07201.75W-"
        kiss_frame = tnc2_to_kiss(tnc2)
        self.assertIsNotNone(kiss_frame)
        result = kiss_to_tnc2(kiss_frame)
        self.assertIsNotNone(result)
        self.assertEqual(result, tnc2)

    def test_with_digipeaters(self):
        """Test packet with digipeater path."""
        tnc2 = "N0CALL-5>APRS,WIDE1-1,WIDE2-1:!4903.50N/07201.75W-test"
        kiss_frame = tnc2_to_kiss(tnc2)
        self.assertIsNotNone(kiss_frame)
        result = kiss_to_tnc2(kiss_frame)
        self.assertIsNotNone(result)
        self.assertEqual(result, tnc2)

    def test_with_digipeated_flag(self):
        """Test packet with has-been-digipeated marker."""
        tnc2 = "N0CALL>APRS,WIDE1*,WIDE2-1:test body"
        kiss_frame = tnc2_to_kiss(tnc2)
        self.assertIsNotNone(kiss_frame)
        result = kiss_to_tnc2(kiss_frame)
        self.assertIsNotNone(result)
        self.assertEqual(result, tnc2)

    def test_with_ssid(self):
        """Test callsigns with SSIDs."""
        tnc2 = "WB4BOR-15>APRS-0:hello"
        kiss_frame = tnc2_to_kiss(tnc2)
        self.assertIsNotNone(kiss_frame)
        result = kiss_to_tnc2(kiss_frame)
        self.assertIsNotNone(result)
        # APRS-0 should round-trip (SSID 0 is explicit)
        self.assertIn("WB4BOR-15", result)

    def test_too_short_frame(self):
        """Test that too-short frames return None."""
        result = kiss_to_tnc2(b'\x00' * 5)
        self.assertIsNone(result)

    def test_empty_frame(self):
        """Test empty input returns None."""
        result = kiss_to_tnc2(b'')
        self.assertIsNone(result)

    def test_raw_frame_without_fend(self):
        """Test raw AX.25 frame without KISS FEND framing."""
        # Encode a packet, then strip the FEND + cmd and trailing FEND
        tnc2 = "N0CALL>APRS:test"
        kiss_frame = tnc2_to_kiss(tnc2)
        # Strip framing: FEND(1) + cmd(1) ... FEND(1)
        raw_ax25 = kiss_frame[2:-1]
        result = kiss_to_tnc2(raw_ax25)
        self.assertIsNotNone(result)
        self.assertEqual(result, tnc2)


class Tnc2ToKissTest(unittest.TestCase):
    """Test TNC-2 format to KISS frame conversion."""

    def test_simple_encode(self):
        """Test basic encoding produces valid KISS frame."""
        result = tnc2_to_kiss("N0CALL>APRS:hello")
        self.assertIsNotNone(result)
        # Must start and end with FEND
        self.assertEqual(result[0], 0xC0)
        self.assertEqual(result[-1], 0xC0)

    def test_invalid_no_colon(self):
        """Test packet without body separator returns None."""
        result = tnc2_to_kiss("N0CALL>APRS")
        self.assertIsNone(result)

    def test_invalid_no_dest(self):
        """Test packet without > separator returns None."""
        result = tnc2_to_kiss("NOCALL:body")
        self.assertIsNone(result)

    def test_port_number(self):
        """Test port number is encoded in command byte."""
        result = tnc2_to_kiss("N0CALL>APRS:hi", port=1)
        # Command byte is (port << 4) = 0x10
        self.assertEqual(result[1], 0x10)

    def test_fesc_encoding(self):
        """Test that FEND/FESC bytes in body are escaped."""
        # Include FEND (0xC0) in body
        body = "test\xc0end"
        result = tnc2_to_kiss("N0CALL>APRS:" + body)
        self.assertIsNotNone(result)
        # The inner data should NOT contain raw FEND (except start/end)
        inner = result[2:-1]  # strip framing
        self.assertNotIn(bytes([0xC0]), inner)

    def test_roundtrip(self):
        """Test full round-trip: TNC-2 -> KISS -> TNC-2."""
        packets = [
            "WB4BOR-9>APU25N,WIDE1-1,WIDE2-2:@092345z4903.50N/07201.75W_",
            "N0CALL>APRS:>status message",
            "KM6LYW-1>APRS,RELAY*,WIDE:!3400.00N/11800.00W#PHG2360",
        ]
        for pkt in packets:
            kiss = tnc2_to_kiss(pkt)
            self.assertIsNotNone(kiss, f"Failed to encode: {pkt}")
            result = kiss_to_tnc2(kiss)
            self.assertIsNotNone(result, f"Failed to decode: {pkt}")
            self.assertEqual(result, pkt)


class Ax25CallTest(unittest.TestCase):
    """Test AX.25 callsign encode/decode helpers."""

    def test_encode_simple(self):
        """Test encoding a simple callsign."""
        result = _encode_ax25_call("N0CALL")
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 7)

    def test_encode_with_ssid(self):
        """Test encoding callsign with SSID."""
        result = _encode_ax25_call("N0CALL-15")
        self.assertIsNotNone(result)

    def test_encode_invalid_ssid(self):
        """Test invalid SSID returns None."""
        result = _encode_ax25_call("N0CALL-16")
        self.assertIsNone(result)

    def test_encode_too_long(self):
        """Test callsign too long returns None."""
        result = _encode_ax25_call("TOOLONGCALL")
        self.assertIsNone(result)

    def test_decode_roundtrip(self):
        """Test encode then decode gives same callsign."""
        calls = ["N0CALL", "WB4BOR-9", "APRS", "WIDE1-1", "KM6LYW-15"]
        for call in calls:
            encoded = _encode_ax25_call(call, is_last=True)
            self.assertIsNotNone(encoded, f"Failed to encode {call}")
            decoded = _decode_ax25_call(encoded)
            self.assertIsNotNone(decoded, f"Failed to decode {call}")
            self.assertEqual(decoded[0], call.upper())


if __name__ == '__main__':
    unittest.main()
