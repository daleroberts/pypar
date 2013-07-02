# PyPAR 

Parallel Python, efficient and scalable parallelism using the message passing interface (MPI).


## Features

- **Python interpreter is not modified**: Parallel python programs need only
  import the pypar module.

- **Easy installation**: This is essentially about compiling and linking
  the C-extension with the local MPI installation. A distutils setup file
  is included.

- **Flexibility**: Pypar allows communication of general Python objects
  of any type.

- **Intuitive API**: The user need only specify what to send and to which
  processor.  Pypar takes care of details about data types and MPI specifics
  such as tags, communicators and buffers.  Receiving is analogous.

- **Efficiency**: Full bandwidth of C-MPI programs is achieved for consecutive
  Numerical arrays. Latency is less than twice that of pure C-MPI programs.
  Test programs to verify this are included (pytiming, ctiming.c)

- **Lightweight**: Pypar consists of just two files: mpiext.c and pypar.py

## Dependencies

- Pypar requires Python, Numpy, C compiler and MPI C library (e.g., OpenMPI)
- Pypar installs with distutils: `python setup.py install`
- Pypar is mostly used on Linux systems, but has been tested on others too

For Ubuntu (and other Debian derivatives) install dependencies as follows:
```sudo apt-get install openmpi-bin libopenmpi-dev python-dev```


## Example

```python
import pypar                                       # Import module and initialise MPI 

proc = pypar.size()                                # Number of processes as specified by mpirun
myid = pypar.rank()                                # Id of of this process (myid in [0, proc-1]) 
node = pypar.get_processor_name()                  # Host name on which current process is running

print 'I am proc %d of %d on node %s' % (myid, proc, node)

if myid == 0:                                      # Actions for process 0:
  msg = 'P0'  
  pypar.send(msg, destination=1)                   # Send message to proces 1 (right hand neighbour)
  msg = pypar.receive(source=proc-1)               # Receive message from last process
      
  print 'Processor 0 received message "%s" from processor %d' % (msg, proc-1)

else:                                              # Actions for all other processes:

  source = myid-1                                  # Source is the process to the left
  destination = (myid+1)%proc                      # Destination is process to the right
                                                   # wrapped so that last processor will 
                                                   # send back to proces 0  
  
  msg = pypar.receive(source)                      # Receive message from source 
  msg = msg + 'P' + str(myid)                      # Update message     
  pypar.send(msg, destination)                     # Send message to destination   

pypar.finalize()                                   # Stop MPI 
```
