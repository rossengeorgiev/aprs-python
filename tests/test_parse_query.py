import pytest
from aprslib.parsing import parse
from aprslib.parsing.query import parse_query
from aprslib.exceptions import ParseError


class TestParseQueryDirect:
    """Test parse_query function directly."""

    def test_simple_aprs_query(self):
        _, result = parse_query("APRS?")
        assert result['format'] == 'query'
        assert result['query_type'] == 'APRS'

    def test_igate_query(self):
        _, result = parse_query("IGATE?")
        assert result['format'] == 'query'
        assert result['query_type'] == 'IGATE'

    def test_wx_query(self):
        _, result = parse_query("WX?")
        assert result['format'] == 'query'
        assert result['query_type'] == 'WX'

    def test_area_qualified_query(self):
        _, result = parse_query("APRS? 3400.00N/11800.00W/0050")
        assert result['format'] == 'query'
        assert result['query_type'] == 'APRS'
        assert abs(result['latitude'] - 34.0) < 0.001
        assert abs(result['longitude'] - (-118.0)) < 0.001
        assert abs(result['range'] - 80.4672) < 0.01

    def test_area_qualified_south_east(self):
        _, result = parse_query("APRS? 3345.00S/15130.00E/0100")
        assert result['latitude'] < 0
        assert result['longitude'] > 0
        assert abs(result['latitude'] - (-33.75)) < 0.001
        assert abs(result['longitude'] - 151.5) < 0.001

    def test_invalid_query_no_type(self):
        with pytest.raises(ParseError):
            parse_query("")

    def test_invalid_query_single_char(self):
        with pytest.raises(ParseError):
            parse_query("X")


class TestParseQueryIntegration:
    """Test query parsing through the full parse() pipeline."""

    def test_simple_aprs_query_packet(self):
        result = parse("N0CALL>APRS:?APRS?")
        assert result['format'] == 'query'
        assert result['query_type'] == 'APRS'
        assert result['from'] == 'N0CALL'
        assert result['to'] == 'APRS'

    def test_area_qualified_packet(self):
        result = parse("N0CALL>APRS:?APRS? 3400.00N/11800.00W/0050")
        assert result['format'] == 'query'
        assert result['query_type'] == 'APRS'
        assert abs(result['latitude'] - 34.0) < 0.001
        assert abs(result['longitude'] - (-118.0)) < 0.001
        assert abs(result['range'] - 80.4672) < 0.01

    def test_igate_query_packet(self):
        result = parse("N0CALL>APRS:?IGATE?")
        assert result['format'] == 'query'
        assert result['query_type'] == 'IGATE'

    def test_wx_query_packet(self):
        result = parse("N0CALL>APRS:?WX?")
        assert result['format'] == 'query'
        assert result['query_type'] == 'WX'
