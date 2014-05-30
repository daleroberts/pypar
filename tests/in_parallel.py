import unittest
import pypar as pp


@pp.test_in_parallel(ncpus=3)
class TestOne(unittest.TestCase):

    def setUp(self):
        self.ncpus = 3

    def test_one(self):
        self.assertTrue(pp.size() == self.ncpus)

    def test_two(self):
        self.assertTrue(True)


@pp.test_in_parallel(ncpus=4)
class TestTwo(unittest.TestCase):

    def setUp(self):
        self.ncpus = 4

    def test_one(self):
        self.assertTrue(pp.size() == self.ncpus)

    def test_two(self):
        self.assertTrue(True)

if __name__ == '__main__':
    pp.test.main()
