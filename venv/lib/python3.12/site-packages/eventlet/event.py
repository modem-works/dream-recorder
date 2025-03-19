from eventlet import hubs
from eventlet.support import greenlets as greenlet

__all__ = ['Event']


class NOT_USED:
    def __repr__(self):
        return 'NOT_USED'


NOT_USED = NOT_USED()


class Event:
    """An abstraction where an arbitrary number of coroutines
    can wait for one event from another.

    Events are similar to a Queue that can only hold one item, but differ
    in two important ways:

    1. calling :meth:`send` never unschedules the current greenthread
    2. :meth:`send` can only be called once; create a new event to send again.

    They are good for communicating results between coroutines, and
    are the basis for how
    :meth:`GreenThread.wait() <eventlet.greenthread.GreenThread.wait>`
    is implemented.

    >>> from eventlet import event
    >>> import eventlet
    >>> evt = event.Event()
    >>> def baz(b):
    ...     evt.send(b + 1)
    ...
    >>> _ = eventlet.spawn_n(baz, 3)
    >>> evt.wait()
    4
    """
    _result = None
    _exc = None

    def __init__(self):
        self._waiters = set()
        self.reset()

    def __str__(self):
        params = (self.__class__.__name__, hex(id(self)),
                  self._result, self._exc, len(self._waiters))
        return '<%s at %s result=%r _exc=%r _waiters[%d]>' % params

    def reset(self):
        # this is kind of a misfeature and doesn't work perfectly well,
        # it's better to create a new event rather than reset an old one
        # removing documentation so that we don't get new use cases for it
        assert self._result is not NOT_USED, 'Trying to re-reset() a fresh event.'
        self._result = NOT_USED
        self._exc = None

    def ready(self):
        """ Return true if the :meth:`wait` call will return immediately.
        Used to avoid waiting for things that might take a while to time out.
        For example, you can put a bunch of events into a list, and then visit
        them all repeatedly, calling :meth:`ready` until one returns ``True``,
        and then you can :meth:`wait` on that one."""
        return self._result is not NOT_USED

    def has_exception(self):
        return self._exc is not None

    def has_result(self):
        return self._result is not NOT_USED and self._exc is None

    def poll(self, notready=None):
        if self.ready():
            return self.wait()
        return notready

    # QQQ make it return tuple (type, value, tb) instead of raising
    # because
    # 1) "poll" does not imply raising
    # 2) it's better not to screw up caller's sys.exc_info() by default
    #    (e.g. if caller wants to calls the function in except or finally)
    def poll_exception(self, notready=None):
        if self.has_exception():
            return self.wait()
        return notready

    def poll_result(self, notready=None):
        if self.has_result():
            return self.wait()
        return notready

    def wait(self, timeout=None):
        """Wait until another coroutine calls :meth:`send`.
        Returns the value the other coroutine passed to :meth:`send`.

        >>> import eventlet
        >>> evt = eventlet.Event()
        >>> def wait_on():
        ...    retval = evt.wait()
        ...    print("waited for {0}".format(retval))
        >>> _ = eventlet.spawn(wait_on)
        >>> evt.send('result')
        >>> eventlet.sleep(0)
        waited for result

        Returns immediately if the event has already occurred.

        >>> evt.wait()
        'result'

        When the timeout argument is present and not None, it should be a floating point number
        specifying a timeout for the operation in seconds (or fractions thereof).
        """
        current = greenlet.getcurrent()
        if self._result is NOT_USED:
            hub = hubs.get_hub()
            self._waiters.add(current)
            timer = None
            if timeout is not None:
                timer = hub.schedule_call_local(timeout, self._do_send, None, None, current)
            try:
                result = hub.switch()
                if timer is not None:
                    timer.cancel()
                return result
            finally:
                self._waiters.discard(current)
        if self._exc is not None:
            current.throw(*self._exc)
        return self._result

    def send(self, result=None, exc=None):
        """Makes arrangements for the waiters to be woken with the
        result and then returns immediately to the parent.

        >>> from eventlet import event
        >>> import eventlet
        >>> evt = event.Event()
        >>> def waiter():
        ...     print('about to wait')
        ...     result = evt.wait()
        ...     print('waited for {0}'.format(result))
        >>> _ = eventlet.spawn(waiter)
        >>> eventlet.sleep(0)
        about to wait
        >>> evt.send('a')
        >>> eventlet.sleep(0)
        waited for a

        It is an error to call :meth:`send` multiple times on the same event.

        >>> evt.send('whoops') # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        AssertionError: Trying to re-send() an already-triggered event.

        Use :meth:`reset` between :meth:`send` s to reuse an event object.
        """
        assert self._result is NOT_USED, 'Trying to re-send() an already-triggered event.'
        self._result = result
        if exc is not None and not isinstance(exc, tuple):
            exc = (exc, )
        self._exc = exc
        hub = hubs.get_hub()
        for waiter in self._waiters:
            hub.schedule_call_global(
                0, self._do_send, self._result, self._exc, waiter)

    def _do_send(self, result, exc, waiter):
        if waiter in self._waiters:
            if exc is None:
                waiter.switch(result)
            else:
                waiter.throw(*exc)

    def send_exception(self, *args):
        """Same as :meth:`send`, but sends an exception to waiters.

        The arguments to send_exception are the same as the arguments
        to ``raise``.  If a single exception object is passed in, it
        will be re-raised when :meth:`wait` is called, generating a
        new stacktrace.

           >>> from eventlet import event
           >>> evt = event.Event()
           >>> evt.send_exception(RuntimeError())
           >>> evt.wait()
           Traceback (most recent call last):
             File "<stdin>", line 1, in <module>
             File "eventlet/event.py", line 120, in wait
               current.throw(*self._exc)
           RuntimeError

        If it's important to preserve the entire original stack trace,
        you must pass in the entire :func:`sys.exc_info` tuple.

           >>> import sys
           >>> evt = event.Event()
           >>> try:
           ...     raise RuntimeError()
           ... except RuntimeError:
           ...     evt.send_exception(*sys.exc_info())
           ...
           >>> evt.wait()
           Traceback (most recent call last):
             File "<stdin>", line 1, in <module>
             File "eventlet/event.py", line 120, in wait
               current.throw(*self._exc)
             File "<stdin>", line 2, in <module>
           RuntimeError

        Note that doing so stores a traceback object directly on the
        Event object, which may cause reference cycles. See the
        :func:`sys.exc_info` documentation.
        """
        # the arguments and the same as for greenlet.throw
        return self.send(None, args)
