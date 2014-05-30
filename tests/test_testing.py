import unittest
import pypar as pp


@pp.test.in_parallel(ncpus=4)
class TestTesting(unittest.TestCase):

    def setUp(self):
        self.x = 31337

    def test_ncpus(self):
        self.assertTrue(pp.size() == 4)

    def test_setup(self):
        self.assertTrue(self.x, 31337)

    def test_assertTrue(self):
        self.assertTrue(True)

    def test_assertEqual(self):
        self.assertEqual("a", "a")

    def test_assertFalse(self):
        self.assertFalse(False)

if __name__ == '__main__':
    pp.test.main()
