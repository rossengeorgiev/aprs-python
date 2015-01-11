import unittest

from aprslib.parse import _parse_comment_telemetry
from aprslib import base91
from random import randint


class ParseCommentTelemetry(unittest.TestCase):
    def setUp(self):
        self.b91max = 91**2 - 1

    def genTelem(self, seq, vals, bits=None):
        data = {
            'seq': seq,
            'vals': vals
            }

        if isinstance(bits, str):
            data.update({'bits': bits})

        return data

    def telemString(self, telem):
        text = ['|']

        # sequence
        if 'seq' in telem:
            text.append(base91.from_decimal(telem['seq'], 2))

        # telemetry channels
        if 'vals' in telem:
            for val in telem['vals']:
                text.append(base91.from_decimal(val, 2))

        # bits as str(11111111)
        if 'bits' in telem:
            val = int(telem['bits'][::-1], 2)
            text.append(base91.from_decimal(val, 2))

        text.append("|")

        return "".join(text)

    def test_random_valid_telemetry(self):
        for i in xrange(100):
            vals = [randint(0, self.b91max) for x in xrange(randint(1, 5))]

            bits = None

            if len(vals) is 5 and randint(1, 10) > 5:
                bits = "{:08b}".format(randint(0, 255))[::-1]

            testData = self.genTelem(i, vals, bits)

            extra, resData = _parse_comment_telemetry(self.telemString(testData))
            resData = resData['telemetry']

            # clean up extra data, so we can compare
            if bits is None:
                del resData['bits']

            resData['vals'] = resData['vals'][:len(vals)]

            self.assertEqual(testData, resData)

    def test_prefix_sufix_glue(self):
        testData = [
            # resulting extra should be 'asdzxc'
            ['asd', '|"!"!|', 'zxc'],
            ['', '|"!"!|', 'zxc'],
            ['asd', '|"!"!|', ''],
            # empty extra
            ['', '|"!"!|', ''],
            # should parse only first occurance of |ss11|
            ['asd', '|"!"!|', '|"!"!|'],
            ['', '|"!"!|', '|"!"!|'],
            ['|aa|', '|"!"!|', '|"!"!|'],
            ['|aa|', '|"!"!|', ''],
            ]

        for datum in testData:
            extra, telem = _parse_comment_telemetry("".join(datum))

            self.assertEqual(datum[0]+datum[2], extra)

    def test_invalid_telemetry(self):
        testData = [
            "||",
            # odd number of characters between pipes
            "|!!|",
            "|!!!|",
            "|!!!!!|",
            "|!!!!!!!|",
            "|!!!!!!!!!|",
            "|!!!!!!!!!!!|",
            "|!!!!!!!!!!!!!|",
            # invalid characters in sequence
            "| a|",
            "|a |",
            "|aa  |",
            "|aaaa  |",
            "|aaaaaa  |",
            "|aaaaaaaa  |",
            "|aaaaaaaaaa  |",
            "|aaaaaaaaaaaa  |",
            "|ss11223344556677|",  # over 8 fields
            ]

        for datum in testData:
            extra, telem = _parse_comment_telemetry(datum)

            self.assertEqual(datum, extra)

    def test_output_format(self):
        parsedOutput = _parse_comment_telemetry("|aabb|")

        self.assertTrue(isinstance(parsedOutput, tuple))
        self.assertTrue(len(parsedOutput) == 2)

        extra, telemetry = parsedOutput

        self.assertTrue(isinstance(extra, str))
        self.assertTrue(isinstance(telemetry, dict))

        self.assertTrue('telemetry' in telemetry)

        self.assertTrue('seq' in telemetry['telemetry'])
        self.assertTrue(isinstance(telemetry['telemetry']['seq'], int))

        self.assertTrue('vals' in telemetry['telemetry'])
        self.assertTrue(isinstance(telemetry['telemetry']['vals'], list))
        self.assertTrue(len(telemetry['telemetry']['vals']) == 5)

        self.assertTrue('bits' in telemetry['telemetry'])
        self.assertTrue(isinstance(telemetry['telemetry']['bits'], str))
        self.assertTrue(len(telemetry['telemetry']['bits']) == 8)
        self.assertTrue(len(telemetry['telemetry']['bits'].replace('0', '')) == 0)


if __name__ == '__main__':
    unittest.main()
