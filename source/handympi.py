#
# Similar to "handythread", but using MPI instead.
#

HAVE_MPI=0
HAVE_PYPAR=0
DEBUG=0
MY_RANK=0

try:
    import pypar as pp   # check to see if we have MPI installed                                                         
    HAVE_PYPAR=1
    MY_RANK=pp.rank()
    
    from pypar_balancer import PyparWork, PyparBalancer
    
    if pp.size() > 1:
        HAVE_MPI=1  # we have pypar, and we're running with more than one node
        
    if DEBUG:
        if HAVE_PYPAR and HAVE_MPI:
            print "Running full MPI"
        elif HAVE_PYPAR:
            print "MPI available, but not enough nodes for master/slave"

    if HAVE_PYPAR and not HAVE_MPI:
        pp.finalize() # not enough nodes to actually run master/slave... shut down MPI now.
        
except:
    if DEBUG:
        import traceback
        traceback.print_exc()
        if HAVE_PYPAR and HAVE_MPI:
            print "Running full MPI"
        elif HAVE_PYPAR:
            print "MPI available, but not enough nodes for master/slave"
        else:
            print "No MPI."
        
if HAVE_MPI:
    class GenericMPI (PyparWork):
    
        def __init__(self, f, l, return_=False, debug=False):
            """
            Used to implement 'foreach' functionality using mpi. 
            Apply a function to each element of list l
            """
            self.applyFunc = f
            self.worklist = l
            self.return_ = return_
            self.debug = debug
            
        def getNumWorkItems(self):
            """
            How many work items are we doing?
            """
            return len(self.worklist)
            
        def calcWorkResult(self, worknum):
            """
            This is where the slave is really doing the work!
            """
            return (worknum, self.applyFunc(self.worklist[worknum]))
            
        def handleWorkResult(self, result, status):
            if self.debug:
                print "Work item completed:", result[0], ':', result[1]

            self.results[result[0]] = result[1]
            self.count += 1
    
        def masterBeforeWork(self):
            """
            Set up someplace to hold the answers...
            """
            self.count = 0
            self.results = [None]*len(self.worklist)
            
    class SimpleMasterSlave(PyparWork):
        """
        Allow true master/slave processing with saved state etc.
        """
    
        def __init__(self, masterClass, slaveClass, workParams):
                self.masterClass = masterClass
                self.slaveClass = slaveClass
                self.worklist = workParams
                
        def getNumWorkItems(self):
            """
            How many work items are we doing?
            """
            return len(self.worklist)
            
        def calcWorkResult(self, worknum):
            """
            This is where the slave is really doing the work!
            """
            return (worknum, self.slaveInstance(self.worklist[worknum]))
            
        def handleWorkResult(self, result, status):
            self.masterInstance(result[0], result[1])
    
        def masterBeforeWork(self):
            """
            Set up someplace to hold the answers...
            """
            self.masterInstance = self.masterClass()
            self.results = [None]*len(self.worklist)
            
        def slaveBeforeWork(self):
            self.slaveInstance = self.slaveClass()

        def getMasterInstance(self):
            """
            Return the master for inspection, etc.
            """
            if hasattr(self, 'masterInstance'):
                return self.masterInstance
            else:
                raise RuntimeError, "Sorry.. you need to 'run' first!"
            
def RunMasterSlave(masterClass, slaveClass, workParams, useMPI=True, finalRun=True):
    """
    This is a generic master/slave runner.
    """
    if HAVE_MPI and useMPI:
        MSRunner = SimpleMasterSlave(masterClass, slaveClass, workParams)
        balancer = PyparBalancer(MSRunner, False)
        balancer.run(finalRun)
        if MY_RANK==0:
            return MSRunner.getMasterInstance()
    else:
        #
        # run serially in case there's no MPI or the called doesn't want it.
        #
        master = masterClass()
        slave = slaveClass()
        for i in range(len(workParams)):
            master(i,slave(workParams[i]))

        return master

def foreach(f, l, useMPI=True, return_=False, debug=False, finalRun=True):
    """
    for each element in list 'l' apply the function 'f'.
    You can force serial operation by setting useMPI to 'False'
    The last time you're call foreach... make sure finalRun=True.
    """
    if HAVE_MPI and useMPI:
        if debug and MY_RANK==0:
            print "Found MPI environment with multiple nodes.. using MPI!"
        GMPI = GenericMPI(f, l, debug=debug)
        balancer = PyparBalancer(GMPI, False) # set this to True to get lots of debugging output
        balancer.run(finalRun)
        if return_:
            if MY_RANK==0:
                return GMPI.results
            else:
                return "You don't get results in this rank!:" + `MY_RANK`
    else:
        #
        # just run serially
        #
        if debug:
            print "No MPI environment with multiple nodes.. evaluating serially."

        if return_:
            results=[]
            for v in l:
                result = f(v)
                if debug:
                    print "Work item completed:", len(results), ':', result
                results.append(result)
            return results
        else:
            for v in l:
                f(v)
            return
