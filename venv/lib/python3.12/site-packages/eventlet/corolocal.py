import weakref

from eventlet import greenthread

__all__ = ['get_ident', 'local']


def get_ident():
    """ Returns ``id()`` of current greenlet.  Useful for debugging."""
    return id(greenthread.getcurrent())


# the entire purpose of this class is to store off the constructor
# arguments in a local variable without calling __init__ directly
class _localbase:
    __slots__ = '_local__args', '_local__greens'

    def __new__(cls, *args, **kw):
        self = object.__new__(cls)
        object.__setattr__(self, '_local__args', (args, kw))
        object.__setattr__(self, '_local__greens', weakref.WeakKeyDictionary())
        if (args or kw) and (cls.__init__ is object.__init__):
            raise TypeError("Initialization arguments are not supported")
        return self


def _patch(thrl):
    greens = object.__getattribute__(thrl, '_local__greens')
    # until we can store the localdict on greenlets themselves,
    # we store it in _local__greens on the local object
    cur = greenthread.getcurrent()
    if cur not in greens:
        # must be the first time we've seen this greenlet, call __init__
        greens[cur] = {}
        cls = type(thrl)
        if cls.__init__ is not object.__init__:
            args, kw = object.__getattribute__(thrl, '_local__args')
            thrl.__init__(*args, **kw)
    object.__setattr__(thrl, '__dict__', greens[cur])


class local(_localbase):
    def __getattribute__(self, attr):
        _patch(self)
        return object.__getattribute__(self, attr)

    def __setattr__(self, attr, value):
        _patch(self)
        return object.__setattr__(self, attr, value)

    def __delattr__(self, attr):
        _patch(self)
        return object.__delattr__(self, attr)
