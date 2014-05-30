import unittest
import numpy as np
import pypar as pp

myid, ncpu = pp.rank(), pp.size()

class TestSendReceive(unittest.TestCase):

    def test_int_array(self):
        N = 17 #Number of elements

        if myid == 0:
            A = np.array(range(N)).astype('i')
            B = np.zeros(N).astype('i')

            pp.send(A, 1, use_buffer=True)
            B = pp.receive(ncpu-1, buffer=B)

            self.assertTrue(np.allclose(A, B))
        else:
            X = np.zeros(N).astype('i')    

            X = pp.receive(myid-1, buffer=X)
            pp.send(X, (myid+1)%ncpu, use_buffer=True)

    def test_longint_array(self):
        N = 17 #Number of elements

        if myid == 0:
            A = np.array(range(N)).astype('l')
            B = np.zeros(N).astype('l')    

            pp.send(A, 1, use_buffer=True)
            B = pp.receive(ncpu-1, buffer=B)

            self.assertTrue(np.allclose(A, B))
        else:
            X = np.zeros(N).astype('l')
            X = pp.receive(myid-1, buffer=X)
            pp.send(X, (myid+1)%ncpu, use_buffer=True)

