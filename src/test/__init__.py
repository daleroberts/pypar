"""
Parallel Testing
"""
import subprocess
import unittest
import inspect
import pickle
import struct
import pypar as pp
import sys
import os

from os.path import abspath

from tblib import pickling_support
pickling_support.install()

MPI_CMD = 'mpirun'


class NullFile(object):

    def write(self, *arg):
        pass

    def writelines(self, *arg):
        pass

    def close(self, *arg):
        pass

    def flush(self, *arg):
        pass

    def isatty(self, *arg):
        return False

    def writeln(self, *arg):
        pass


class WorkerResult(unittest.result.TestResult):

    def __init__(self, stream, descriptions, verbosity):
        super(WorkerResult, self).__init__()
        self.stream = stream
        sys.stdout = NullFile()
        sys.stderr = NullFile()

    def addSuccess(self, test):
        self._send_event('addSuccess', test)

    def addError(self, test, err):
        self._send_event('addError', test, err)

    def addFailure(self, test, err):
        self._send_event('addFailure', test, err)

    def _send_event(self, event, test, err=None):
        rank = pp.rank()
        if rank > 0:
            return

        data = pickle.dumps((rank, str(event), err))
        data = data.encode("latin1")
        header = struct.pack("!I", len(data))

        self.stream.write(header + data)
        self.stream.flush()


class WorkerTestRunner(unittest.runner.TextTestRunner):

    def __init__(self, *args, **kwargs):
        super(WorkerTestRunner, self).__init__(*args, **kwargs)

    def run(self, test):
        result = self._makeResult()
        startTestRun = getattr(result, 'startTestRun', None)
        if startTestRun is not None:
            startTestRun()
        try:
            test(result)
        finally:
            stopTestRun = getattr(result, 'stopTestRun', None)
            if stopTestRun is not None:
                stopTestRun()
        return result


class TestProxy(object):

    def __init__(self, testfile, testname, test, ncpus=2):
        self.testfile = testfile
        self.testname = testname
        self.test = test
        self.ncpus = ncpus

    def __call__(self, result=None):
        from six import reraise

        argv = [MPI_CMD, '-c', str(self.ncpus), 'python',
                self.testfile, self.testname]
        popen = subprocess.Popen(argv,
                                 cwd=os.getcwd(),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)

        try:
            stdout = popen.stdout
            while True:
                header = stdout.read(4)
                if not header:
                    break
                if len(header) < 4:
                    raise Exception("short message header %r" % header)
                request_len = struct.unpack("!I", header)[0]
                data = stdout.read(request_len)
                if len(data) < request_len:
                    raise Exception("short message body (want %d, got %d)\n" %
                                    (request_len, len(data)) +
                                    "Something went wrong\nMessage: %s" %
                                    (header + data).decode("latin1"))
                data = data.decode("latin1")
                rank, event, err = pickle.loads(data)
                if err is not None:
                    reraise(*err)
        finally:
            popen.wait()


def in_parallel(ncpus=2):
    def proxy(cls):
        def proxy_fn(name, fn):
            def new_fn(self):
                testname = '%s.%s' % (cls.__name__, name)
                testfile = abspath(inspect.getsourcefile(fn))
                proxy = TestProxy(testfile, testname, self, ncpus)
                return proxy()
            return new_fn
        if not os.getenv('OMPI_COMM_WORLD_RANK'):
            for name, fn in inspect.getmembers(cls, predicate=inspect.ismethod):
                if 'test' in name.lower():
                    thefunction = proxy_fn(name, fn)
                    thefunction.__name__ = name
                    setattr(cls, name, thefunction)
        return cls
    return proxy


def main():
    if os.getenv('OMPI_COMM_WORLD_RANK'):
        import atexit
        atexit.register(pp.finalize)
        runner = WorkerTestRunner(resultclass=WorkerResult)
        unittest.main(testRunner=runner)
    else:
        unittest.main()
