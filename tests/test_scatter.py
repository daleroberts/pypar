import unittest
import pypar as pp
import numpy as np


@pp.test.in_parallel(ncpus=4)
class TestScatter(unittest.TestCase):

    def test_string(self):
        myid, ncpu = pp.rank(), pp.size()
        data = 'ABCDEFGHIJKLMNOP'  # Length = 16
        NP = len(data) / ncpu
        X = ' ' * NP

        pp.scatter(data, 0, buffer=X)  # With buffer
        Y = pp.scatter(data, 0)  # With buffer automatically created

        self.assertEqual(X, Y)
        self.assertEqual(Y, data[myid * NP:(myid + 1) * NP])
        self.assertEqual(X, data[myid * NP:(myid + 1) * NP])

    def test_array(self):
        myid, ncpu = pp.rank(), pp.size()
        N = 16
        NP = N / ncpu
        data = np.array(range(N)).astype('i')
        X = np.zeros(NP).astype('i')

        pp.scatter(data, 0, buffer=X)  # With buffer
        Y = pp.scatter(data, 0)  # With buffer automatically created

        self.assertTrue(np.allclose(X, Y))
        self.assertTrue(np.allclose(X, data[myid * NP:(myid + 1) * NP]))
        self.assertTrue(np.allclose(Y, data[myid * NP:(myid + 1) * NP]))

    def test_without_root(self):
        myid, ncpu = pp.rank(), pp.size()
        N = 16
        NP = N / ncpu
        data = np.array(range(N)).astype('i')
        X = np.zeros(NP).astype('i')

        pp.scatter(data, buffer=X)  # With buffer
        Y = pp.scatter(data)  # With buffer automatically created

        self.assertTrue(np.allclose(X, Y))
        self.assertTrue(np.allclose(X, data[myid * NP:(myid + 1) * NP]))
        self.assertTrue(np.allclose(Y, data[myid * NP:(myid + 1) * NP]))

    def test_diff_master(self):
        myid, ncpu = pp.rank(), pp.size()
        N = 16
        NP = N / ncpu

        check = np.array(range(N)).astype('i')
        X = np.zeros(NP).astype('i')

        data = np.empty(N, 'i')

        if myid == 0:  # only generated on master
            data = np.array(range(N)).astype('i')

        pp.scatter(data, 0, buffer=X)  # With buffer
        Y = pp.scatter(data, 0)  # With buffer automatically created

        self.assertTrue(np.allclose(X, Y))
        self.assertTrue(np.allclose(X, check[myid * NP:(myid + 1) * NP]))
        self.assertTrue(np.allclose(Y, check[myid * NP:(myid + 1) * NP]))


if __name__ == '__main__':
    pp.test.main()
