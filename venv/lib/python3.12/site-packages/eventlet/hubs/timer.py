import traceback

import eventlet.hubs
from eventlet.support import greenlets as greenlet
import io

""" If true, captures a stack trace for each timer when constructed.  This is
useful for debugging leaking timers, to find out where the timer was set up. """
_g_debug = False


class Timer:
    def __init__(self, seconds, cb, *args, **kw):
        """Create a timer.
            seconds: The minimum number of seconds to wait before calling
            cb: The callback to call when the timer has expired
            *args: The arguments to pass to cb
            **kw: The keyword arguments to pass to cb

        This timer will not be run unless it is scheduled in a runloop by
        calling timer.schedule() or runloop.add_timer(timer).
        """
        self.seconds = seconds
        self.tpl = cb, args, kw
        self.called = False
        if _g_debug:
            self.traceback = io.StringIO()
            traceback.print_stack(file=self.traceback)

    @property
    def pending(self):
        return not self.called

    def __repr__(self):
        secs = getattr(self, 'seconds', None)
        cb, args, kw = getattr(self, 'tpl', (None, None, None))
        retval = "Timer(%s, %s, *%s, **%s)" % (
            secs, cb, args, kw)
        if _g_debug and hasattr(self, 'traceback'):
            retval += '\n' + self.traceback.getvalue()
        return retval

    def copy(self):
        cb, args, kw = self.tpl
        return self.__class__(self.seconds, cb, *args, **kw)

    def schedule(self):
        """Schedule this timer to run in the current runloop.
        """
        self.called = False
        self.scheduled_time = eventlet.hubs.get_hub().add_timer(self)
        return self

    def __call__(self, *args):
        if not self.called:
            self.called = True
            cb, args, kw = self.tpl
            try:
                cb(*args, **kw)
            finally:
                try:
                    del self.tpl
                except AttributeError:
                    pass

    def cancel(self):
        """Prevent this timer from being called. If the timer has already
        been called or canceled, has no effect.
        """
        if not self.called:
            self.called = True
            eventlet.hubs.get_hub().timer_canceled(self)
            try:
                del self.tpl
            except AttributeError:
                pass

    # No default ordering in 3.x. heapq uses <
    # FIXME should full set be added?
    def __lt__(self, other):
        return id(self) < id(other)


class LocalTimer(Timer):

    def __init__(self, *args, **kwargs):
        self.greenlet = greenlet.getcurrent()
        Timer.__init__(self, *args, **kwargs)

    @property
    def pending(self):
        if self.greenlet is None or self.greenlet.dead:
            return False
        return not self.called

    def __call__(self, *args):
        if not self.called:
            self.called = True
            if self.greenlet is not None and self.greenlet.dead:
                return
            cb, args, kw = self.tpl
            cb(*args, **kw)

    def cancel(self):
        self.greenlet = None
        Timer.cancel(self)
