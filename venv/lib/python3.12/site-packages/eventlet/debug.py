"""The debug module contains utilities and functions for better
debugging Eventlet-powered applications."""

import os
import sys
import linecache
import re
import inspect

__all__ = ['spew', 'unspew', 'format_hub_listeners', 'format_hub_timers',
           'hub_listener_stacks', 'hub_exceptions', 'tpool_exceptions',
           'hub_prevent_multiple_readers', 'hub_timer_stacks',
           'hub_blocking_detection']

_token_splitter = re.compile(r'\W+')


class Spew:

    def __init__(self, trace_names=None, show_values=True):
        self.trace_names = trace_names
        self.show_values = show_values

    def __call__(self, frame, event, arg):
        if event == 'line':
            lineno = frame.f_lineno
            if '__file__' in frame.f_globals:
                filename = frame.f_globals['__file__']
                if (filename.endswith('.pyc') or
                        filename.endswith('.pyo')):
                    filename = filename[:-1]
                name = frame.f_globals['__name__']
                line = linecache.getline(filename, lineno)
            else:
                name = '[unknown]'
                try:
                    src = inspect.getsourcelines(frame)
                    line = src[lineno]
                except OSError:
                    line = 'Unknown code named [%s].  VM instruction #%d' % (
                        frame.f_code.co_name, frame.f_lasti)
            if self.trace_names is None or name in self.trace_names:
                print('%s:%s: %s' % (name, lineno, line.rstrip()))
                if not self.show_values:
                    return self
                details = []
                tokens = _token_splitter.split(line)
                for tok in tokens:
                    if tok in frame.f_globals:
                        details.append('%s=%r' % (tok, frame.f_globals[tok]))
                    if tok in frame.f_locals:
                        details.append('%s=%r' % (tok, frame.f_locals[tok]))
                if details:
                    print("\t%s" % ' '.join(details))
        return self


def spew(trace_names=None, show_values=False):
    """Install a trace hook which writes incredibly detailed logs
    about what code is being executed to stdout.
    """
    sys.settrace(Spew(trace_names, show_values))


def unspew():
    """Remove the trace hook installed by spew.
    """
    sys.settrace(None)


def format_hub_listeners():
    """ Returns a formatted string of the current listeners on the current
    hub.  This can be useful in determining what's going on in the event system,
    especially when used in conjunction with :func:`hub_listener_stacks`.
    """
    from eventlet import hubs
    hub = hubs.get_hub()
    result = ['READERS:']
    for l in hub.get_readers():
        result.append(repr(l))
    result.append('WRITERS:')
    for l in hub.get_writers():
        result.append(repr(l))
    return os.linesep.join(result)


def format_hub_timers():
    """ Returns a formatted string of the current timers on the current
    hub.  This can be useful in determining what's going on in the event system,
    especially when used in conjunction with :func:`hub_timer_stacks`.
    """
    from eventlet import hubs
    hub = hubs.get_hub()
    result = ['TIMERS:']
    for l in hub.timers:
        result.append(repr(l))
    return os.linesep.join(result)


def hub_listener_stacks(state=False):
    """Toggles whether or not the hub records the stack when clients register
    listeners on file descriptors.  This can be useful when trying to figure
    out what the hub is up to at any given moment.  To inspect the stacks
    of the current listeners, call :func:`format_hub_listeners` at critical
    junctures in the application logic.
    """
    from eventlet import hubs
    hubs.get_hub().set_debug_listeners(state)


def hub_timer_stacks(state=False):
    """Toggles whether or not the hub records the stack when timers are set.
    To inspect the stacks of the current timers, call :func:`format_hub_timers`
    at critical junctures in the application logic.
    """
    from eventlet.hubs import timer
    timer._g_debug = state


def hub_prevent_multiple_readers(state=True):
    """Toggle prevention of multiple greenlets reading from a socket

    When multiple greenlets read from the same socket it is often hard
    to predict which greenlet will receive what data.  To achieve
    resource sharing consider using ``eventlet.pools.Pool`` instead.

    But if you really know what you are doing you can change the state
    to ``False`` to stop the hub from protecting against this mistake.
    """
    from eventlet.hubs import hub, get_hub
    from eventlet.hubs import asyncio
    if not state and isinstance(get_hub(), asyncio.Hub):
        raise RuntimeError("Multiple readers are not yet supported by asyncio hub")
    hub.g_prevent_multiple_readers = state


def hub_exceptions(state=True):
    """Toggles whether the hub prints exceptions that are raised from its
    timers.  This can be useful to see how greenthreads are terminating.
    """
    from eventlet import hubs
    hubs.get_hub().set_timer_exceptions(state)
    from eventlet import greenpool
    greenpool.DEBUG = state


def tpool_exceptions(state=False):
    """Toggles whether tpool itself prints exceptions that are raised from
    functions that are executed in it, in addition to raising them like
    it normally does."""
    from eventlet import tpool
    tpool.QUIET = not state


def hub_blocking_detection(state=False, resolution=1):
    """Toggles whether Eventlet makes an effort to detect blocking
    behavior in an application.

    It does this by telling the kernel to raise a SIGALARM after a
    short timeout, and clearing the timeout every time the hub
    greenlet is resumed.  Therefore, any code that runs for a long
    time without yielding to the hub will get interrupted by the
    blocking detector (don't use it in production!).

    The *resolution* argument governs how long the SIGALARM timeout
    waits in seconds.  The implementation uses :func:`signal.setitimer`
    and can be specified as a floating-point value.
    The shorter the resolution, the greater the chance of false
    positives.
    """
    from eventlet import hubs
    assert resolution > 0
    hubs.get_hub().debug_blocking = state
    hubs.get_hub().debug_blocking_resolution = resolution
    if not state:
        hubs.get_hub().block_detect_post()
