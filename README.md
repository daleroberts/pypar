[![Logo](https://raw.githubusercontent.com/daleroberts/pypar/master/doc/logo.png)](https://raw.githubusercontent.com/daleroberts/pypar/master/doc/logo.png)

**PyPar** is a python library that provides efficient and scalable parallelism using the message passing interface (MPI) to handle **big data** and **highly computational problems**.

[![Build Status](https://travis-ci.org/daleroberts/pypar.svg?branch=master)](https://travis-ci.org/daleroberts/pypar)

## Example

A simple 'pass the parcel' example.

```python
import pypar as pp

ncpus = pp.size()
rank = pp.rank()
node = pp.get_processor_name()

print 'I am rank %d of %d on node %s' % (rank, ncpus, node)

if rank == 0:
  msh = 'P0'
  pp.send(msg, destination=1)
  msg = pp.receive(source=rank-1)
  print 'Processor 0 received message "%s" from rank %d' % (msg, rank-1)
else:
  source = rank-1
  destination = (rank+1) % ncpus
  msg = pp.receive(source)
  msg = msg + 'P' + str(rank)
  pypar.send(msg, destination)

pp.finalize()
```
