"""Tests for Object and Item packet construction."""
import unittest
from aprslib.packets.object import ObjectReport, ItemReport


class ObjectReportTest(unittest.TestCase):
    """Test ObjectReport packet construction."""

    def test_basic_object(self):
        """Test basic object construction."""
        obj = ObjectReport()
        obj.fromcall = 'N0CALL'
        obj.tocall = 'APRS'
        obj.name = 'Test'
        obj.latitude = 49.0583
        obj.longitude = -72.0292
        obj.symbol_table = '/'
        obj.symbol = '-'
        obj.timestamp = '092345z'

        body = obj._serialize_body()
        self.assertTrue(body.startswith(';Test     *'))
        self.assertIn('092345z', body)

    def test_name_padding(self):
        """Object names are padded to 9 characters."""
        obj = ObjectReport()
        obj.name = 'Hi'
        obj.timestamp = '010000z'
        body = obj._serialize_body()
        # ;Hi       *
        self.assertEqual(body[1:10], 'Hi       ')

    def test_name_truncation(self):
        """Object names longer than 9 raise ValueError."""
        obj = ObjectReport()
        obj.name = 'VeryLongObjectName'
        obj.timestamp = '010000z'
        with self.assertRaises(ValueError):
            obj._serialize_body()

    def test_killed_object(self):
        """Killed objects use _ marker."""
        obj = ObjectReport()
        obj.name = 'Dead'
        obj.alive = False
        obj.timestamp = '010000z'
        body = obj._serialize_body()
        # ;Dead     _
        self.assertEqual(body[10], '_')

    def test_live_object(self):
        """Live objects use * marker."""
        obj = ObjectReport()
        obj.name = 'Live'
        obj.alive = True
        obj.timestamp = '010000z'
        body = obj._serialize_body()
        self.assertEqual(body[10], '*')

    def test_with_altitude(self):
        """Object with altitude includes /A= comment."""
        obj = ObjectReport()
        obj.name = 'Balloon'
        obj.latitude = 35.0
        obj.longitude = -106.0
        obj.altitude = 3048.0  # meters
        obj.timestamp = '010000z'
        body = obj._serialize_body()
        self.assertIn('/A=010000', body)

    def test_full_packet_string(self):
        """Test full packet serialization."""
        obj = ObjectReport()
        obj.fromcall = 'N0CALL'
        obj.tocall = 'APRS'
        obj.path = ['WIDE1-1']
        obj.name = 'Test'
        obj.latitude = 49.0583
        obj.longitude = -72.0292
        obj.symbol_table = '/'
        obj.symbol = '-'
        obj.timestamp = '092345z'
        pkt = str(obj)
        self.assertTrue(pkt.startswith('N0CALL>APRS,WIDE1-1:'))
        self.assertIn(';Test     *', pkt)

    def test_latitude_validation(self):
        """Invalid latitude raises ValueError."""
        obj = ObjectReport()
        with self.assertRaises(ValueError):
            obj.latitude = 91.0

    def test_longitude_validation(self):
        """Invalid longitude raises ValueError."""
        obj = ObjectReport()
        with self.assertRaises(ValueError):
            obj.longitude = 181.0


class ItemReportTest(unittest.TestCase):
    """Test ItemReport packet construction."""

    def test_basic_item(self):
        """Test basic item construction."""
        item = ItemReport()
        item.name = 'Test'
        item.latitude = 49.0583
        item.longitude = -72.0292
        item.symbol_table = '/'
        item.symbol = '-'
        body = item._serialize_body()
        self.assertTrue(body.startswith(')Test!'))

    def test_item_no_padding(self):
        """Item names shorter than 3 raise ValueError."""
        item = ItemReport()
        item.name = 'Hi'
        with self.assertRaises(ValueError):
            item._serialize_body()

    def test_killed_item(self):
        """Killed items use _ marker."""
        item = ItemReport()
        item.name = 'Dead'
        item.alive = False
        body = item._serialize_body()
        self.assertTrue(body.startswith(')Dead_'))

    def test_item_with_comment(self):
        """Item with comment text."""
        item = ItemReport()
        item.name = 'Fuel'
        item.latitude = 35.0
        item.longitude = -106.0
        item.comment = 'Open 24hrs'
        body = item._serialize_body()
        self.assertIn('Open 24hrs', body)


if __name__ == '__main__':
    unittest.main()
