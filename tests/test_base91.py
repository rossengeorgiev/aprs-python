import unittest

from aprslib import base91


class a_FromDecimal(unittest.TestCase):
    def test_valid_input(self):
        testData = [
            [0, '!'],
            [1, '"'],
            [90, '{'],
            [91, '"!'],
            ]

        # 91**1 = "!
        # 91**2 = "!!
        # 91**3 = "!!!
        # etc
        testData += [[91**i, '"' + '!'*i] for i in xrange(20)]

        for n, expected in testData:
            self.assertEqual(expected, base91.from_decimal(n))

    def test_invalid_input_type(self):
        testData = ['0', '1', 1.0, None, [0]]

        for n in testData:
            self.assertRaises(ValueError, base91.from_decimal, n)

    def test_invalid_input_range(self):
        testData = [-10000, -5, -1]

        for n in testData:
            self.assertRaises(ValueError, base91.from_decimal, n)

    def test_valid_padding(self):
        testData = [1, 2, 5, 10, 100]

        for n in testData:
            self.assertEqual(n, len(base91.from_decimal(0, n)))

    def test_invalid_padding(self):
        testData = [0, -1, -100]

        for n in testData:
            self.assertRaises(ValueError, base91.from_decimal, 0, padding=n)


class b_ToDecimal(unittest.TestCase):
    def test_valid_input(self):
        testData = [
            [0, '!'],
            [0, '!!!!!!!!!'],
            [1, '"'],
            [1, '!!"'],
            [90, '{'],
            [90, '!{'],
            [91, '"!'],
            [91, '!!!"!'],
            ]

        # 91**1 = "!
        # 91**2 = "!!
        # 91**3 = "!!!
        # etc
        testData += [[91**i, '"' + '!'*i] for i in xrange(20)]

        for expected, n in testData:
            self.assertEqual(expected, base91.to_decimal(n))

    def test_invalid_input_type(self):
        testData = [-1, 0, 5, unicode('a'), None, ['d']]

        for n in testData:
            self.assertRaises(TypeError, base91.to_decimal, n)

    def test_invalid_input(self):
        # test for every value outside of the accepted range
        testData = [chr(i) for i in range(ord('!'))+range(ord('{')+1, 256)]

        # same as above, except each value is prefix with a valid char
        testData += ['!'+c for c in testData]

        for n in testData:
            self.assertRaises(ValueError, base91.to_decimal, n)


class c_Both(unittest.TestCase):
    def test_from_decimal_to_decimal(self):
        for number in xrange(91**2 + 5):
            text = base91.from_decimal(number)
            result = base91.to_decimal(text)

            self.assertEqual(result, number)

    def test_stability(self):
        for number in xrange(50):
            largeN = 91 ** number
            text = base91.from_decimal(largeN)
            result = base91.to_decimal(text)

            self.assertEqual(result, largeN)


if __name__ == '__main__':
    unittest.main()
