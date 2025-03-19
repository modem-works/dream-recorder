import importlib
import inspect
import os
import warnings

from eventlet import patcher
from eventlet.support import greenlets as greenlet


__all__ = ["use_hub", "get_hub", "get_default_hub", "trampoline"]

threading = patcher.original('threading')
_threadlocal = threading.local()


# order is important, get_default_hub returns first available from here
builtin_hub_names = ('epolls', 'kqueue', 'poll', 'selects')
builtin_hub_modules = tuple(importlib.import_module('eventlet.hubs.' + name) for name in builtin_hub_names)


class HubError(Exception):
    pass


def get_default_hub():
    """Select the default hub implementation based on what multiplexing
    libraries are installed.  The order that the hubs are tried is:

    * epoll
    * kqueue
    * poll
    * select

    .. include:: ../../doc/source/common.txt
    .. note :: |internal|
    """
    for mod in builtin_hub_modules:
        if mod.is_available():
            return mod

    raise HubError('no built-in hubs are available: {}'.format(builtin_hub_modules))


def use_hub(mod=None):
    """Use the module *mod*, containing a class called Hub, as the
    event hub. Usually not required; the default hub is usually fine.

    `mod` can be an actual hub class, a module, a string, or None.

    If `mod` is a class, use it directly.
    If `mod` is a module, use `module.Hub` class
    If `mod` is a string and contains either '.' or ':'
    then `use_hub` uses 'package.subpackage.module:Class' convention,
    otherwise imports `eventlet.hubs.mod`.
    If `mod` is None, `use_hub` uses the default hub.

    Only call use_hub during application initialization,
    because it resets the hub's state and any existing
    timers or listeners will never be resumed.

    These two threadlocal attributes are not part of Eventlet public API:
    - `threadlocal.Hub` (capital H) is hub constructor, used when no hub is currently active
    - `threadlocal.hub` (lowercase h) is active hub instance
    """
    if mod is None:
        mod = os.environ.get('EVENTLET_HUB', None)
    if mod is None:
        mod = get_default_hub()
    if hasattr(_threadlocal, 'hub'):
        del _threadlocal.hub

    classname = ''
    if isinstance(mod, str):
        assert mod.strip(), "Need to specify a hub"
        if '.' in mod or ':' in mod:
            modulename, _, classname = mod.strip().partition(':')
        else:
            modulename = 'eventlet.hubs.' + mod
        mod = importlib.import_module(modulename)

    if hasattr(mod, 'is_available'):
        if not mod.is_available():
            raise Exception('selected hub is not available on this system mod={}'.format(mod))
    else:
        msg = '''Please provide `is_available()` function in your custom Eventlet hub {mod}.
It must return bool: whether hub supports current platform. See eventlet/hubs/{{epoll,kqueue}} for example.
'''.format(mod=mod)
        warnings.warn(msg, DeprecationWarning, stacklevel=3)

    hubclass = mod
    if not inspect.isclass(mod):
        hubclass = getattr(mod, classname or 'Hub')

    _threadlocal.Hub = hubclass


def get_hub():
    """Get the current event hub singleton object.

    .. note :: |internal|
    """
    try:
        hub = _threadlocal.hub
    except AttributeError:
        try:
            _threadlocal.Hub
        except AttributeError:
            use_hub()
        hub = _threadlocal.hub = _threadlocal.Hub()
    return hub


# Lame middle file import because complex dependencies in import graph
from eventlet import timeout


def trampoline(fd, read=None, write=None, timeout=None,
               timeout_exc=timeout.Timeout,
               mark_as_closed=None):
    """Suspend the current coroutine until the given socket object or file
    descriptor is ready to *read*, ready to *write*, or the specified
    *timeout* elapses, depending on arguments specified.

    To wait for *fd* to be ready to read, pass *read* ``=True``; ready to
    write, pass *write* ``=True``. To specify a timeout, pass the *timeout*
    argument in seconds.

    If the specified *timeout* elapses before the socket is ready to read or
    write, *timeout_exc* will be raised instead of ``trampoline()``
    returning normally.

    .. note :: |internal|
    """
    t = None
    hub = get_hub()
    current = greenlet.getcurrent()
    assert hub.greenlet is not current, 'do not call blocking functions from the mainloop'
    assert not (
        read and write), 'not allowed to trampoline for reading and writing'
    try:
        fileno = fd.fileno()
    except AttributeError:
        fileno = fd
    if timeout is not None:
        def _timeout(exc):
            # This is only useful to insert debugging
            current.throw(exc)
        t = hub.schedule_call_global(timeout, _timeout, timeout_exc)
    try:
        if read:
            listener = hub.add(hub.READ, fileno, current.switch, current.throw, mark_as_closed)
        elif write:
            listener = hub.add(hub.WRITE, fileno, current.switch, current.throw, mark_as_closed)
        try:
            return hub.switch()
        finally:
            hub.remove(listener)
    finally:
        if t is not None:
            t.cancel()


def notify_close(fd):
    """
    A particular file descriptor has been explicitly closed. Register for any
    waiting listeners to be notified on the next run loop.
    """
    hub = get_hub()
    hub.notify_close(fd)


def notify_opened(fd):
    """
    Some file descriptors may be closed 'silently' - that is, by the garbage
    collector, by an external library, etc. When the OS returns a file descriptor
    from an open call (or something similar), this may be the only indication we
    have that the FD has been closed and then recycled.
    We let the hub know that the old file descriptor is dead; any stuck listeners
    will be disabled and notified in turn.
    """
    hub = get_hub()
    hub.mark_as_reopened(fd)


class IOClosed(IOError):
    pass
