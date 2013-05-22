import unittest
import unittest.result as result
import subprocess
import argparse
import atexit
import sys
import os
import re

class PyparTestResult(result.TestResult):

    def __init__(self, stream, descriptions, verbosity):
        super(PyparTestResult, self).__init__()
        self.stream = stream

    def addSuccess(self, test):
        super(PyparTestResult, self).addSuccess(test)
        self.stream.write("@%i:%s:OK" % (pp.rank(), test.id()))
        self.stream.writeln('')
        self.stream.flush()

    def addError(self, test, err):
        super(PyparTestResult, self).addError(test, err)
        self.stream.write("@%i:%s:ERROR" % (pp.rank(), test.id()))
        self.stream.writeln('')
        self.stream.flush()

    def addFailure(self, test, err):
        super(PyparTestResult, self).addFailure(test, err)
        self.stream.write("@%i:%s:FAIL" % (pp.rank(), test.id()))
        self.stream.writeln('')
        self.stream.flush()

def collect_results(output):
    test_results = {}

    testre = re.compile('@(\d):(\w+(?:\.\w+){1,}):([A-Z]+)')

    for line in output.splitlines():
        match = testre.search(line)
        if match:
            test, rank, outcome = match.group(2,1,3)
            if not test_results.has_key(test):
                test_results[test] = {}
            test_results[test][int(rank)] = outcome

    return test_results

def run():
    tests = unittest.defaultTestLoader.discover('.', pattern='unittest*.py')
    tr = unittest.runner.TextTestRunner(resultclass=PyparTestResult)
    # Fingers crossed that tests run in same order on each worker
    tr.run(tests)

def mpirun(ncpu=2):
    print('Running tests with %i workers.' % ncpu)
    proc = subprocess.Popen(['mpirun', '-tag-output', '-n', str(ncpu), 'python', __file__],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()

    results = collect_results(stderr)
    tests = sorted(results.keys())
    maxlen = str(max([len(s) for s in tests]) + 2)

    for test in sorted(results.keys()):
        outcomes = ['%i:%s' % (k,v) for k,v in sorted(results[test].items())]
        print(('{0:<' + maxlen + '} {1}').format(test, ' '.join(outcomes)))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run Pypar unittests.')
    parser.add_argument('-n', '--n', default=2)
    args = parser.parse_args()

    if os.getenv('OMPI_COMM_WORLD_RANK') \
    or os.getenv('LAMRANK'):
        import pypar as pp
        atexit.register(pp.finalize)
        run()
    else:
        mpirun(int(args.n))


