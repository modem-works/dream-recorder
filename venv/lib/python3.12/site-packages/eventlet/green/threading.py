"""Implements the standard threading module, using greenthreads."""
import eventlet
from eventlet.green import thread
from eventlet.green import time
from eventlet.support import greenlets as greenlet

__patched__ = ['_start_new_thread', '_allocate_lock',
               '_sleep', 'local', 'stack_size', 'Lock', 'currentThread',
               'current_thread', '_after_fork', '_shutdown']

__patched__ += ['get_ident', '_set_sentinel']

__orig_threading = eventlet.patcher.original('threading')
__threadlocal = __orig_threading.local()
__patched_enumerate = None


eventlet.patcher.inject(
    'threading',
    globals(),
    ('_thread', thread),
    ('time', time))


_count = 1


class _GreenThread:
    """Wrapper for GreenThread objects to provide Thread-like attributes
    and methods"""

    def __init__(self, g):
        global _count
        self._g = g
        self._name = 'GreenThread-%d' % _count
        _count += 1

    def __repr__(self):
        return '<_GreenThread(%s, %r)>' % (self._name, self._g)

    def join(self, timeout=None):
        return self._g.wait()

    def getName(self):
        return self._name
    get_name = getName

    def setName(self, name):
        self._name = str(name)
    set_name = setName

    name = property(getName, setName)

    ident = property(lambda self: id(self._g))

    def isAlive(self):
        return True
    is_alive = isAlive

    daemon = property(lambda self: True)

    def isDaemon(self):
        return self.daemon
    is_daemon = isDaemon


__threading = None


def _fixup_thread(t):
    # Some third-party packages (lockfile) will try to patch the
    # threading.Thread class with a get_name attribute if it doesn't
    # exist. Since we might return Thread objects from the original
    # threading package that won't get patched, let's make sure each
    # individual object gets patched too our patched threading.Thread
    # class has been patched. This is why monkey patching can be bad...
    global __threading
    if not __threading:
        __threading = __import__('threading')

    if (hasattr(__threading.Thread, 'get_name') and
            not hasattr(t, 'get_name')):
        t.get_name = t.getName
    return t


def current_thread():
    global __patched_enumerate
    g = greenlet.getcurrent()
    if not g:
        # Not currently in a greenthread, fall back to standard function
        return _fixup_thread(__orig_threading.current_thread())

    try:
        active = __threadlocal.active
    except AttributeError:
        active = __threadlocal.active = {}

    g_id = id(g)
    t = active.get(g_id)
    if t is not None:
        return t

    # FIXME: move import from function body to top
    # (jaketesler@github) Furthermore, I was unable to have the current_thread() return correct results from
    # threading.enumerate() unless the enumerate() function was a) imported at runtime using the gross __import__() call
    # and b) was hot-patched using patch_function().
    # https://github.com/eventlet/eventlet/issues/172#issuecomment-379421165
    if __patched_enumerate is None:
        __patched_enumerate = eventlet.patcher.patch_function(__import__('threading').enumerate)
    found = [th for th in __patched_enumerate() if th.ident == g_id]
    if found:
        return found[0]

    # Add green thread to active if we can clean it up on exit
    def cleanup(g):
        del active[g_id]
    try:
        g.link(cleanup)
    except AttributeError:
        # Not a GreenThread type, so there's no way to hook into
        # the green thread exiting. Fall back to the standard
        # function then.
        t = _fixup_thread(__orig_threading.current_thread())
    else:
        t = active[g_id] = _GreenThread(g)

    return t


currentThread = current_thread
