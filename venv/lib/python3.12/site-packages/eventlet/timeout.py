# Copyright (c) 2009-2010 Denis Bilenko, denis.bilenko at gmail com
# Copyright (c) 2010 Eventlet Contributors (see AUTHORS)
# and licensed under the MIT license:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import functools
import inspect

import eventlet
from eventlet.support import greenlets as greenlet
from eventlet.hubs import get_hub

__all__ = ['Timeout', 'with_timeout', 'wrap_is_timeout', 'is_timeout']

_MISSING = object()

# deriving from BaseException so that "except Exception as e" doesn't catch
# Timeout exceptions.


class Timeout(BaseException):
    """Raises *exception* in the current greenthread after *timeout* seconds.

    When *exception* is omitted or ``None``, the :class:`Timeout` instance
    itself is raised. If *seconds* is None, the timer is not scheduled, and is
    only useful if you're planning to raise it directly.

    Timeout objects are context managers, and so can be used in with statements.
    When used in a with statement, if *exception* is ``False``, the timeout is
    still raised, but the context manager suppresses it, so the code outside the
    with-block won't see it.
    """

    def __init__(self, seconds=None, exception=None):
        self.seconds = seconds
        self.exception = exception
        self.timer = None
        self.start()

    def start(self):
        """Schedule the timeout.  This is called on construction, so
        it should not be called explicitly, unless the timer has been
        canceled."""
        assert not self.pending, \
            '%r is already started; to restart it, cancel it first' % self
        if self.seconds is None:  # "fake" timeout (never expires)
            self.timer = None
        elif self.exception is None or isinstance(self.exception, bool):  # timeout that raises self
            self.timer = get_hub().schedule_call_global(
                self.seconds, greenlet.getcurrent().throw, self)
        else:  # regular timeout with user-provided exception
            self.timer = get_hub().schedule_call_global(
                self.seconds, greenlet.getcurrent().throw, self.exception)
        return self

    @property
    def pending(self):
        """True if the timeout is scheduled to be raised."""
        if self.timer is not None:
            return self.timer.pending
        else:
            return False

    def cancel(self):
        """If the timeout is pending, cancel it.  If not using
        Timeouts in ``with`` statements, always call cancel() in a
        ``finally`` after the block of code that is getting timed out.
        If not canceled, the timeout will be raised later on, in some
        unexpected section of the application."""
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None

    def __repr__(self):
        classname = self.__class__.__name__
        if self.pending:
            pending = ' pending'
        else:
            pending = ''
        if self.exception is None:
            exception = ''
        else:
            exception = ' exception=%r' % self.exception
        return '<%s at %s seconds=%s%s%s>' % (
            classname, hex(id(self)), self.seconds, exception, pending)

    def __str__(self):
        """
        >>> raise Timeout  # doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
            ...
        Timeout
        """
        if self.seconds is None:
            return ''
        if self.seconds == 1:
            suffix = ''
        else:
            suffix = 's'
        if self.exception is None or self.exception is True:
            return '%s second%s' % (self.seconds, suffix)
        elif self.exception is False:
            return '%s second%s (silent)' % (self.seconds, suffix)
        else:
            return '%s second%s (%s)' % (self.seconds, suffix, self.exception)

    def __enter__(self):
        if self.timer is None:
            self.start()
        return self

    def __exit__(self, typ, value, tb):
        self.cancel()
        if value is self and self.exception is False:
            return True

    @property
    def is_timeout(self):
        return True


def with_timeout(seconds, function, *args, **kwds):
    """Wrap a call to some (yielding) function with a timeout; if the called
    function fails to return before the timeout, cancel it and return a flag
    value.
    """
    timeout_value = kwds.pop("timeout_value", _MISSING)
    timeout = Timeout(seconds)
    try:
        try:
            return function(*args, **kwds)
        except Timeout as ex:
            if ex is timeout and timeout_value is not _MISSING:
                return timeout_value
            raise
    finally:
        timeout.cancel()


def wrap_is_timeout(base):
    '''Adds `.is_timeout=True` attribute to objects returned by `base()`.

    When `base` is class, attribute is added as read-only property. Returns `base`.
    Otherwise, it returns a function that sets attribute on result of `base()` call.

    Wrappers make best effort to be transparent.
    '''
    if inspect.isclass(base):
        base.is_timeout = property(lambda _: True)
        return base

    @functools.wraps(base)
    def fun(*args, **kwargs):
        ex = base(*args, **kwargs)
        ex.is_timeout = True
        return ex
    return fun


if isinstance(__builtins__, dict):  # seen when running tests on py310, but HOW??
    _timeout_err = __builtins__.get('TimeoutError', Timeout)
else:
    _timeout_err = getattr(__builtins__, 'TimeoutError', Timeout)


def is_timeout(obj):
    return bool(getattr(obj, 'is_timeout', False)) or isinstance(obj, _timeout_err)
