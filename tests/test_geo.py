"""Tests for geographic utilities (distance, direction, position resolution)."""
import unittest
from aprslib.geo import distance, direction, position_resolution


class DistanceTest(unittest.TestCase):
    """Test great circle distance calculation."""

    def test_same_point(self):
        """Distance from point to itself is 0."""
        self.assertAlmostEqual(distance(49.0, -72.0, 49.0, -72.0), 0.0)

    def test_known_distance(self):
        """Test known distance: NYC to London ~5570 km."""
        d = distance(40.7128, -74.0060, 51.5074, -0.1278)
        self.assertAlmostEqual(d, 5570.0, delta=50)  # within 50km

    def test_antipodal(self):
        """Distance between antipodal points ~ 20015 km (half circumference)."""
        d = distance(0.0, 0.0, 0.0, 180.0)
        self.assertAlmostEqual(d, 20015.0, delta=100)

    def test_equator_one_degree(self):
        """One degree of longitude at equator ~ 111.2 km."""
        d = distance(0.0, 0.0, 0.0, 1.0)
        self.assertAlmostEqual(d, 111.2, delta=1.0)

    def test_short_distance(self):
        """Short distance (< 1 km) between nearby points."""
        # ~100m difference in latitude
        d = distance(49.0000, -72.0, 49.0009, -72.0)
        self.assertAlmostEqual(d, 0.1, delta=0.02)


class DirectionTest(unittest.TestCase):
    """Test bearing calculation."""

    def test_due_north(self):
        """Direction due north = 0 degrees."""
        bearing = direction(49.0, -72.0, 50.0, -72.0)
        self.assertAlmostEqual(bearing, 0.0, delta=1.0)

    def test_due_east(self):
        """Direction due east = 90 degrees."""
        bearing = direction(0.0, 0.0, 0.0, 1.0)
        self.assertAlmostEqual(bearing, 90.0, delta=0.1)

    def test_due_south(self):
        """Direction due south = 180 degrees."""
        bearing = direction(50.0, -72.0, 49.0, -72.0)
        self.assertAlmostEqual(bearing, 180.0, delta=1.0)

    def test_due_west(self):
        """Direction due west = 270 degrees."""
        bearing = direction(0.0, 1.0, 0.0, 0.0)
        self.assertAlmostEqual(bearing, 270.0, delta=0.1)

    def test_range_0_360(self):
        """Bearing is always in 0-360 range."""
        bearing = direction(0.0, 0.0, -1.0, -1.0)
        self.assertGreaterEqual(bearing, 0.0)
        self.assertLess(bearing, 360.0)


class PositionResolutionTest(unittest.TestCase):
    """Test position resolution calculation."""

    def test_full_precision(self):
        """Full precision (no spaces) = ~18.52m."""
        res = position_resolution("4903.50")
        self.assertAlmostEqual(res, 18.52, delta=0.01)

    def test_one_space(self):
        """One trailing space = ~185.2m."""
        res = position_resolution("4903.5 ")
        self.assertAlmostEqual(res, 185.2, delta=0.1)

    def test_two_spaces(self):
        """Two trailing spaces = ~1852m."""
        res = position_resolution("4903.  ")
        self.assertAlmostEqual(res, 1852.0, delta=1.0)

    def test_three_spaces(self):
        """Three trailing spaces = ~18520m."""
        res = position_resolution("490 .  ")
        self.assertAlmostEqual(res, 18520.0, delta=10.0)

    def test_four_spaces(self):
        """Four trailing spaces = ~111120m (1 degree)."""
        res = position_resolution("49  .  ")
        self.assertAlmostEqual(res, 111120.0, delta=100.0)

    def test_no_dot(self):
        """No decimal point returns None."""
        res = position_resolution("4903")
        self.assertIsNone(res)

    def test_empty(self):
        """Empty string returns None."""
        self.assertIsNone(position_resolution(""))
        self.assertIsNone(position_resolution(None))


if __name__ == '__main__':
    unittest.main()
