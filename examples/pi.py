"""
Compute the value of Pi using Monte Carlo. This demonstrates
the use of the scatter and gather functions.

Dale Roberts <dale.o.roberts@gmail.com>
"""

import numpy as np
import pypar as pp

N = 100000
ncpu = pp.size()
myid = pp.rank()

def mc_pi(points):
    inside = 0
    for x, y in points:
        if x**2 + y**2 <= 1:
            inside += 1
    return 4*float(inside)/len(points)

points = np.random.random((N, 2)) #FIXME: this is done on each cpu

mypoints = pp.scatter(points, 0)
mypi = np.array([mc_pi(mypoints)]) #FIXME: casting float as np.array for gather

pi = sum(pp.gather(mypi, 0)) / ncpu

if myid == 0:
    abserror = abs(pi - np.pi)
    print("pi: %.16f abs error: %.16f" % (pi, abserror))

pp.finalize()
