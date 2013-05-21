"""
Simple scatter example.

Dale Roberts <dale.o.roberts@gmail.com>
"""

import numpy as np
import pypar as pp

ncpu = pp.size()
myid = pp.rank()

N = 16
NP = N/ncpu

if myid == 0:
    data = np.arange(N, dtype='i')
else:
    data = np.empty(N, dtype='i')

X = np.zeros(NP, dtype='i')

pp.scatter(data, 0, buffer=X) # With buffer
Y = pp.scatter(data, 0) # With buffer automatically created

print "id: %i X: %s" % (myid, X)
print "id: %i Y: %s" % (myid, Y)

pp.finalize()
