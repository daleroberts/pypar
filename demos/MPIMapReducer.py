"""
MapReduce-over-MPI sample

Run as (as exsample)
   mpirun -np 2 python MPIMapReducer.py
  (perhaps try number of processors more than 2)
  

GPC JAN 2013
"""

import sys

try:
    import numpy
except:
    raise Exception, 'Module numpy must be present to run pypar'
        
try:
    import pypar
except:
    raise Exception, 'Module pypar must be present to run parallel'

import logging
LOGFMT = 'pid: %(process)d - %(asctime)s - %(levelname)s:%(message)s'
logging.basicConfig(format=LOGFMT, level=logging.INFO)

class MPIMapReducer():

    def __init__(self, aWorkList):  
       
        self.WORKTAG = 1
        self.DIETAG =  2
        
        self.MPI_myid =    pypar.rank()
        self.MPI_numproc = pypar.size()
        self.MPI_node =    pypar.get_processor_name()

        self.works = aWorkList
        self.numWorks = len(self.works)

        self.reduceFunction = None
        self.mapFunction = None
        self.result = None
   
        if self.MPI_numproc < 2:
            pypar.finalize()
            if self.MPI_myid == 0:
                raise Exception, 'ERROR: Number of processors must be greater than 2.'

    def master(self):
        self.numCompleted = 0
        self.mapList = list()
        logging.info('[MASTER]: started processor %d of %d on node %s: number of works: %d'%(self.MPI_myid, self.MPI_numproc, self.MPI_node, self.numWorks))

        # start slaves distributing the first work slot             
        rounder = 0
        if self.MPI_numproc <= self.numWorks:
            rounder = 1
        for i in range(min(self.MPI_numproc, self.numWorks)-rounder):
            work = self.works[i]
            pypar.send(work, destination=i+1, tag=self.WORKTAG)
            logging.debug('[MASTER]: sent work "%s" to node %d' %(work, i+1))

        # dispatch the remaining work slots on dynamic load-balancing policy
        # the quicker to do the job, the more jobs it takes
        for work in self.works[self.MPI_numproc-1:]:
            result, status = pypar.receive(source=pypar.any_source, tag=self.WORKTAG,
                                           return_status=True)
            logging.debug('[MASTER]: received result "%s" from node %d'%(result, status.source))
                  
            self.mapList.append(result)
            self.numCompleted += 1           
            logging.debug('[MASTER]: done : %d' %self.numCompleted)       
        
            pypar.send(work, destination=status.source, tag=self.WORKTAG)
            logging.debug('[MASTER]: sent work "%s" to node %d' %(work, status.source))

        # all works have been dispatched out
        logging.debug('[MASTER]: toDo : %d' %self.numWorks)
        logging.debug('[MASTER]: done : %d' %self.numCompleted)

        # I've still to take into the remaining completions
        while (self.numCompleted < self.numWorks):
            result, status = pypar.receive(source=pypar.any_source, tag=self.WORKTAG,
                                       return_status=True)
            logging.debug('[MASTER]: received (final) result "%s" from node %d'%(result, status.source))
            
            self.mapList.append(result)            
            self.numCompleted += 1
            logging.debug('[MASTER]: %d completed' %self.numCompleted)

        logging.debug('[MASTER]: about to terminate slaves')

        # Tell slaves to stop working
        for i in range(1, self.MPI_numproc):
            pypar.send('#', destination=i, tag=self.DIETAG)
            logging.debug('[MASTER]: sent termination signal to node %d' %(i, ))

        # call the reduce function
        logging.info('[MASTER]: about to run reduce')
        res = self.reduceFunction(self.mapList)
        return res

    def slave(self):

        logging.debug('[SLAVE %d]: started processor %d of %d on node %s'%(self.MPI_myid, self.MPI_myid, self.MPI_numproc, self.MPI_node))

        while True:
            inputMsg, status = pypar.receive(source=0,
                                       tag=pypar.any_tag,
                                       return_status=True)
            logging.debug('[SLAVE %d]: received work "%s" with tag %d from node %d' %(self.MPI_myid, inputMsg, status.tag, status.source))

            if (status.tag == self.DIETAG):
                logging.debug('[SLAVE %d]: received termination from node %d'%(self.MPI_myid, 0))
                return
            else:
                logging.debug('[SLAVE %d]: received work "%s" to map' %(self.MPI_myid, inputMsg))
                resultMsg = self.mapFunction(inputMsg)
                pypar.send(resultMsg, destination=0, tag=self.WORKTAG)
                logging.debug('[SLAVE %d]: sent result "%s" to node %d'%(self.MPI_myid, resultMsg, 0))

        
    def setReduce(self, aFunction):
        self.reduceFunction = aFunction
        
    def setMap(self, aFunction):
        self.mapFunction = aFunction

    def runMapReduce(self):
        if self.MPI_myid == 0:
            self.result = self.master()
        else:
            self.slave()

        pypar.finalize()
        logging.debug('[PROCESS %d]: MPI environment finalized.'%(self.MPI_myid, ))
        return
        
    def getResult(self):
        if self.MPI_myid == 0:
            return self.result
        else:
            logging.debug('[SLAVE %d]: ending.'%(self.MPI_myid, ))
            sys.exit(0)





if __name__ == '__main__':
    
    def mapFn(anInput):
        return 'X' + anInput

    def reduceFn(aList):
        return ''.join(aList)    
    
    workList = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']*10

    logging.debug('starting mpimapreducer with %d works.'%(len(workList),))
    
    m2r = MPIMapReducer(workList)        
    m2r.setMap(mapFn)
    m2r.setReduce(reduceFn)
    # here's the beef
    m2r.runMapReduce()
    
    lenmr = len(m2r.getResult())
    print "MAPREDUCE :", lenmr
    logging.debug('ended mpimapreduce')
    
    logging.info('starting sequential evaluation')
    lenseq = len(''.join('X' + item for item in workList))
    print "SEQUENTIAL:", lenseq
    logging.info('ending sequential evaluation')
    
    # the result must be the same
    assert lenmr == lenseq

