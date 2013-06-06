"""
Functional parallel tools
=========================

"""
import pypar as pp
import itertools


def distributed_slice(iterable):
    """
    Distribute a 'slice'able iterable across workers.
    """
    P = pp.size()
    if P == 1:
        for el in iterable:
            yield el
    else:
        if pp.rank() == 0:
            lst = list(iterable)
            N = len(lst)
            for p in range(1, P):
                Nlo, Nhi = pp.balance(N, P, p)
                pp.send(lst[Nlo:Nhi], p)

            Nlo, Nhi = pp.balance(N, P, 0)
            for el in lst[Nlo:Nhi]:
                yield el
        else:
            llst = pp.receive(0)
            for el in llst:
                yield el


def distributed_generator(iterable):
    """
    Distribute the values from a generator across workers.
    """
    RUN, DIE = range(2)
    P = pp.size()
    if P == 1:
        for el in iterable:
            yield el
    else:
        if pp.rank() == 0:
            it = iter(iterable)
            while True:
                try:
                    first = next(it)
                    for p in range(1, P):
                        pp.send(next(it), p, tag=RUN)
                    yield first
                except StopIteration:
                    for p in range(1, P):
                        pp.send(666, p, tag=DIE)
                    break
        else:
            while True:
                el, status = pp.receive(0, tag=pp.any_tag, return_status=True)
                if status.tag == DIE:
                    break
                yield el


def distributed(iterable):
    """
    Distribute an iterable across processors.
    """
    if hasattr(iterable, '__getslice__'):
        return distributed_slice(iterable)
    else:
        return distributed_generator(iterable)


def collected(iterable):
    """
    Collect iterables back to the master.
    """
    P = pp.size()
    if P == 1:
        for el in iterable:
            yield el
    else:
        if pp.rank() == 0:
            results = list(iterable)
            for p in range(1, P):
                pres = pp.receive(p)
                results.extend(pres)
            for el in results:
                yield el
        else:
            pp.send(list(iterable), 0)


def balanced(iterable):
    """
    Balance an iterator over the processors.
    """
    P, p = pp.size(), pp.rank()
    return itertools.islice(iterable, p, None, P)
