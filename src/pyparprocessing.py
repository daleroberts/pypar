import copy_reg
import types


RUN = 1
DIE = 2


def mute_worker_output(f):
    import os
    import sys
    import logging
    try:
        if pp.rank() > 0:
            logging.debug('I am worker %i, muting myself' % pp.rank())
            # Mute logging
            logger = logging.getLogger()
            logger.disabled = True
            # Mute stdout, stderr
            devnull = open(os.devnull, 'w')
            def newf(*args, **kwargs):
                old_stderr, old_stdout = sys.stderr, sys.stdout
                sys.stderr = devnull
                sys.stdout = devnull
                try:
                    return f(*args, **kwargs)
                finally:
                    sys.stderr, sys.stdout = old_stderr, old_stdout
            return newf
    except NameError: # no pypar
        pass
    # else do nothing
    return f


def _pickle_MethodType(method):
    funcname = method.__name__
    obj = method.__self__
    cls = method.im_class
    return _unpickle_MethodType, (funcname, obj, cls)


def _unpickle_MethodType(funcname, obj, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[funcname]
        except KeyError:
            pass
        else:
            break
    return func.__get__(obj, cls)


def _pickle_FunctionType(function):
    import marshal
    name = function.__name__
    code = function.func_code
    dump = marshal.dumps(code)
    return _unpickle_FunctionType, (name, dump,)


def _unpickle_FunctionType(name, dump):
    import marshal
    code = marshal.loads(dump)
    return types.FunctionType(code, globals(), name)


copy_reg.pickle(types.MethodType, _pickle_MethodType, _unpickle_MethodType)
copy_reg.pickle(types.FunctionType, _pickle_FunctionType, _unpickle_FunctionType)


class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class PyparPool(object):

    __metaclass__ = Singleton

    def __init__(self, processes=None, initializer=None, initargs=(), maxtasksperchild=None):
        self.initializer = initializer
        self.initargs = initargs
        self.maxtasks = maxtasksperchild
        self.state = RUN

        if pp.rank() == 0 and pp.size() > 1:
            # in case a generator is not consumed and exit occurs
            import atexit
            atexit.register(self.terminate)

    def _imap_master(self, func, iterable):
        tasks = ((i, func, (x,), {}) for i, x in enumerate(iterable))
        results = list()

        nsent = 0
        nrecv = 0

        # Give all workers a task to start with
        for i in range(1, pp.size()):
            try:
                pp.send(tasks.next(), destination=i, tag=RUN)
                nsent += 1
            except StopIteration:
                pass

        # Give a new task once they have finished
        for task in tasks:
            result, status = pp.receive(source=pp.any_source, tag=RUN,
                                        return_status=True)
            nrecv += 1
            pp.send(task, destination=status.source, tag=RUN)
            nsent += 1
            yield result

        # Collect the final results
        while (nrecv < nsent):
            result, status = pp.receive(source=pp.any_source, tag=RUN,
                                        return_status=True)
            nrecv += 1
            yield result

        if self.state == DIE:
            self.terminate()

    def imap(self, f, work):
        assert self.state == RUN
        assert pp.size() > 1 and pp.rank() == 0
        return self._imap_master(f, work)

    def close(self):
        if self.state == RUN:
            self.state = DIE

    def terminate(self):
        for i in range(1, pp.size()):
            pp.send(666, destination=i, tag=DIE)
        pp.finalize()


class DummyPool(object):

    __metaclass__ = Singleton

    def __init__(self, processes=None, initializer=None, initargs=(), maxtasksperchild=None):
        self.initializer = initializer
        self.initargs = initargs
        self.maxtasks = maxtasksperchild

    def imap(self, f, work):
        if self.initializer is not None:
            self.initializer(*self.initargs)

        import itertools
        return itertools.imap(f, work)

    def close(self):
        pass

    def terminate(self):
        pass


def worker(initializer=None, initargs=(), maxtasks=None):
    assert maxtasks is None or (type(maxtasks) == int and maxtasks > 0)

    if initializer is not None:
        initializer(*initargs)

    completed = 0
    while maxtasks is None or (maxtasks and completed < maxtasks):
        try:
            task, status = pp.receive(
                source=0, tag=pp.any_tag, return_status=True)
        except:
            break

        if (status.tag == DIE):
            break

        i, func, args, kwds = task

        try:
            result = func(*args, **kwds)
        except Exception, e:
            result = e

        pp.send(result, destination=0, tag=RUN)
        completed += 1

    pp.finalize()

    import sys
    sys.exit(0)


Pool = DummyPool


def start(initializer=None, initargs=(), maxtasks=None):
    global Pool
    try:
        # make pypar available
        global pp
        import pypar as pp

        if pp.size() > 1:
            Pool = PyparPool
            if pp.rank() > 0:
                worker(initializer, initargs, maxtasks)
        else:
            # fallback to multiprocessing
            print 'Using multiprocessing'
            pp.finalize()
            import multiprocessing as mp
            Pool = mp.Pool

    except ImportError: # no pypar
        return


