import time, sys, numpy
from mpi4py import MPI

consistency_check = False

comm = MPI.COMM_WORLD

def linfit(x, y):
  """
  Fit a and b to the model y = ax + b. Return a,b,variance.
  """
  
  Sx = Sy = SSoN = SxoN = norm = varest = 0.0
  N = len(x)
  assert len(y) == N, "x and y must have same length"
  
  for i in range(N):
    #print("x,y = %f, %f\n",x[i],y[i])
    Sx  = Sx + x[i]
    Sy  = Sy + y[i]
  
  SxoN = Sx/N
  
  a = 0.0 
  for i in range(N):
    t    = x[i] - SxoN
    SSoN = SSoN + t*t
    a    = a + t*y[i]


  a = a/SSoN            # a = (N Sxy - SxSy)/(NSxx - Sx^2) */
  b = (Sy - Sx*a)/N
  
  # Quality - variance estimate \sum_i r_i^2 /(m-n) 
  for i in range(N):  
    norm = norm + float(x[i])*x[i]
    res = y[i] - a*x[i] - b
    varest = varest + res*res

  varest = varest/norm/(N-2)
  return a, b, varest




#--------------------------------------------------------------
# Main program
#
MAXI  = 10         # Number of blocks 
MAXM  = 500000     # Largest block 
BLOCK = MAXM/MAXI  # Block size 

repeats = 10
msgid = 0
vanilla = 0 #Select vanilla mode (slower but general)

numprocs = comm.Get_size()
myid = comm.Get_rank()
processor_name = MPI.Get_processor_name()

if myid == 0:
  # Main process - Create message, pass on, verify correctness and log timing
  #
  print "MAXM = %d, number of processors = %d" %(MAXM, numprocs)
  print "Measurements are repeated %d times for reliability" %repeats

if numprocs < 2:
  print "Program needs at least two processors - aborting\n"
  sys.exit(2)
   
comm.barrier() #Synchronize all before timing   
print "I am process %d on %s" %(myid,processor_name)


#Initialise data and timings
#

try:
  from numpy.random import uniform, seed
  seed(17)
  A = uniform(0.0,100.0,MAXM)
except:
  print 'problem with RandomArray'
  from numpy import ones, Float
  A = ones(MAXM).astype('f')
  
elsize = A.itemsize
#print elsize

noelem  = [0]*MAXI
bytes   = [0]*MAXI         
avgtime = [0.0]*MAXI         
mintime = [ 1000000.0]*MAXI      
maxtime = [-1000000.0]*MAXI            

if myid == 0:   
  # Determine timer overhead 
  cpuOH = 1.0;
  for k in range(repeats):   # Repeat to get reliable timings 
    t1 = MPI.Wtime()
    t2 = MPI.Wtime()
    if t2-t1 < cpuOH: cpuOH = t2-t1
    
  print "Timing overhead is %f seconds.\n" %cpuOH         

# Pass msg circularly   
for k in range(repeats):
  if myid == 0:
    print "Run %d of %d" %(k+1,repeats)
    
  for i in range(MAXI):
    m=BLOCK*i+1       
   
    noelem[i] = m
   
    comm.barrier() # Synchronize 
   
    if myid == 0:
      #
      # Main process
      #
      t1 = MPI.Wtime()

      comm.Send(A[:m], dest=1, tag=0)
      C = numpy.empty_like(A[:m])
      comm.Recv(C, source=numprocs-1, tag=0)
       
      t2 = MPI.Wtime() - t1 - cpuOH
      t2 = t2/numprocs
      avgtime[i] = avgtime[i] + t2
      if t2 < mintime[i]: mintime[i] = t2
      if t2 > maxtime[i]: maxtime[i] = t2

      # Uncomment to verify integrity of data
      # However, this may affect accuracy of timings for some reason.
      #
      if consistency_check:
        assert numpy.alltrue(C == A[:m])
    else:
      #
      # Parallel process - get msg and pass it on
      #
      C = numpy.empty_like(A[:m])
      comm.Recv(C, source=myid-1, tag=0)
      comm.Send(A[:m], dest=(myid+1)%numprocs, tag=0)

# Output stats
#
if myid == 0:
  print "Bytes transferred   time (micro seconds)"
  print "                    min        avg        max "     
  print "----------------------------------------------"
     
  for i in range(MAXI):
    avgtime[i] = avgtime[i]/repeats*1.0e6 #Average micro seconds
    mintime[i] = mintime[i]*1.0e6         #Min micro seconds       
    maxtime[i] = maxtime[i]*1.0e6         #Min micro seconds              
          
    m = noelem[i]
    bytes[i] = elsize*noelem[i]       
      
    print "%10d    %10d %10d %10d" %(bytes[i], mintime[i], avgtime[i], maxtime[i]) 


  Tbw, Tlat, varest = linfit(bytes, mintime)
  print "\nLinear regression on best timings (t = t_l + t_b * bytes):\n",
  print "  t_b = %f\n  t_l = %f" %(Tbw,Tlat)
  print "  Estimated relative variance = %.9f\n" %varest
       
  print "Estimated bandwith (1/t_b):  %.3f Mb/s" %(1.0/Tbw)   
  print "Estimated latency:           %d micro s" %int(mintime[0]-bytes[0]*Tbw)  
