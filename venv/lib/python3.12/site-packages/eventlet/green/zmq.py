"""The :mod:`zmq` module wraps the :class:`Socket` and :class:`Context`
found in :mod:`pyzmq <zmq>` to be non blocking.
"""
__zmq__ = __import__('zmq')
import eventlet.hubs
from eventlet.patcher import slurp_properties
from eventlet.support import greenlets as greenlet

__patched__ = ['Context', 'Socket']
slurp_properties(__zmq__, globals(), ignore=__patched__)

from collections import deque

try:
    # alias XREQ/XREP to DEALER/ROUTER if available
    if not hasattr(__zmq__, 'XREQ'):
        XREQ = DEALER
    if not hasattr(__zmq__, 'XREP'):
        XREP = ROUTER
except NameError:
    pass


class LockReleaseError(Exception):
    pass


class _QueueLock:
    """A Lock that can be acquired by at most one thread. Any other
    thread calling acquire will be blocked in a queue. When release
    is called, the threads are awoken in the order they blocked,
    one at a time. This lock can be required recursively by the same
    thread."""

    def __init__(self):
        self._waiters = deque()
        self._count = 0
        self._holder = None
        self._hub = eventlet.hubs.get_hub()

    def __nonzero__(self):
        return bool(self._count)

    __bool__ = __nonzero__

    def __enter__(self):
        self.acquire()

    def __exit__(self, type, value, traceback):
        self.release()

    def acquire(self):
        current = greenlet.getcurrent()
        if (self._waiters or self._count > 0) and self._holder is not current:
            # block until lock is free
            self._waiters.append(current)
            self._hub.switch()
            w = self._waiters.popleft()

            assert w is current, 'Waiting threads woken out of order'
            assert self._count == 0, 'After waking a thread, the lock must be unacquired'

        self._holder = current
        self._count += 1

    def release(self):
        if self._count <= 0:
            raise LockReleaseError("Cannot release unacquired lock")

        self._count -= 1
        if self._count == 0:
            self._holder = None
            if self._waiters:
                # wake next
                self._hub.schedule_call_global(0, self._waiters[0].switch)


class _BlockedThread:
    """Is either empty, or represents a single blocked thread that
    blocked itself by calling the block() method. The thread can be
    awoken by calling wake(). Wake() can be called multiple times and
    all but the first call will have no effect."""

    def __init__(self):
        self._blocked_thread = None
        self._wakeupper = None
        self._hub = eventlet.hubs.get_hub()

    def __nonzero__(self):
        return self._blocked_thread is not None

    __bool__ = __nonzero__

    def block(self, deadline=None):
        if self._blocked_thread is not None:
            raise Exception("Cannot block more than one thread on one BlockedThread")
        self._blocked_thread = greenlet.getcurrent()

        if deadline is not None:
            self._hub.schedule_call_local(deadline - self._hub.clock(), self.wake)

        try:
            self._hub.switch()
        finally:
            self._blocked_thread = None
            # cleanup the wakeup task
            if self._wakeupper is not None:
                # Important to cancel the wakeup task so it doesn't
                # spuriously wake this greenthread later on.
                self._wakeupper.cancel()
                self._wakeupper = None

    def wake(self):
        """Schedules the blocked thread to be awoken and return
        True. If wake has already been called or if there is no
        blocked thread, then this call has no effect and returns
        False."""
        if self._blocked_thread is not None and self._wakeupper is None:
            self._wakeupper = self._hub.schedule_call_global(0, self._blocked_thread.switch)
            return True
        return False


class Context(__zmq__.Context):
    """Subclass of :class:`zmq.Context`
    """

    def socket(self, socket_type):
        """Overridden method to ensure that the green version of socket is used

        Behaves the same as :meth:`zmq.Context.socket`, but ensures
        that a :class:`Socket` with all of its send and recv methods set to be
        non-blocking is returned
        """
        if self.closed:
            raise ZMQError(ENOTSUP)
        return Socket(self, socket_type)


def _wraps(source_fn):
    """A decorator that copies the __name__ and __doc__ from the given
    function
    """
    def wrapper(dest_fn):
        dest_fn.__name__ = source_fn.__name__
        dest_fn.__doc__ = source_fn.__doc__
        return dest_fn
    return wrapper


# Implementation notes: Each socket in 0mq contains a pipe that the
# background IO threads use to communicate with the socket. These
# events are important because they tell the socket when it is able to
# send and when it has messages waiting to be received. The read end
# of the events pipe is the same FD that getsockopt(zmq.FD) returns.
#
# Events are read from the socket's event pipe only on the thread that
# the 0mq context is associated with, which is the native thread the
# greenthreads are running on, and the only operations that cause the
# events to be read and processed are send(), recv() and
# getsockopt(zmq.EVENTS). This means that after doing any of these
# three operations, the ability of the socket to send or receive a
# message without blocking may have changed, but after the events are
# read the FD is no longer readable so the hub may not signal our
# listener.
#
# If we understand that after calling send() a message might be ready
# to be received and that after calling recv() a message might be able
# to be sent, what should we do next? There are two approaches:
#
#  1. Always wake the other thread if there is one waiting. This
#  wakeup may be spurious because the socket might not actually be
#  ready for a send() or recv().  However, if a thread is in a
#  tight-loop successfully calling send() or recv() then the wakeups
#  are naturally batched and there's very little cost added to each
#  send/recv call.
#
# or
#
#  2. Call getsockopt(zmq.EVENTS) and explicitly check if the other
#  thread should be woken up. This avoids spurious wake-ups but may
#  add overhead because getsockopt will cause all events to be
#  processed, whereas send and recv throttle processing
#  events. Admittedly, all of the events will need to be processed
#  eventually, but it is likely faster to batch the processing.
#
# Which approach is better? I have no idea.
#
# TODO:
# - Support MessageTrackers and make MessageTracker.wait green

_Socket = __zmq__.Socket
_Socket_recv = _Socket.recv
_Socket_send = _Socket.send
_Socket_send_multipart = _Socket.send_multipart
_Socket_recv_multipart = _Socket.recv_multipart
_Socket_send_string = _Socket.send_string
_Socket_recv_string = _Socket.recv_string
_Socket_send_pyobj = _Socket.send_pyobj
_Socket_recv_pyobj = _Socket.recv_pyobj
_Socket_send_json = _Socket.send_json
_Socket_recv_json = _Socket.recv_json
_Socket_getsockopt = _Socket.getsockopt


class Socket(_Socket):
    """Green version of :class:``zmq.core.socket.Socket``.

    The following three methods are always overridden:
        * send
        * recv
        * getsockopt
    To ensure that the ``zmq.NOBLOCK`` flag is set and that sending or receiving
    is deferred to the hub (using :func:``eventlet.hubs.trampoline``) if a
    ``zmq.EAGAIN`` (retry) error is raised.

    For some socket types, the following methods are also overridden:
        * send_multipart
        * recv_multipart
    """

    def __init__(self, context, socket_type):
        super().__init__(context, socket_type)

        self.__dict__['_eventlet_send_event'] = _BlockedThread()
        self.__dict__['_eventlet_recv_event'] = _BlockedThread()
        self.__dict__['_eventlet_send_lock'] = _QueueLock()
        self.__dict__['_eventlet_recv_lock'] = _QueueLock()

        def event(fd):
            # Some events arrived at the zmq socket. This may mean
            # there's a message that can be read or there's space for
            # a message to be written.
            send_wake = self._eventlet_send_event.wake()
            recv_wake = self._eventlet_recv_event.wake()
            if not send_wake and not recv_wake:
                # if no waiting send or recv thread was woken up, then
                # force the zmq socket's events to be processed to
                # avoid repeated wakeups
                _Socket_getsockopt(self, EVENTS)

        hub = eventlet.hubs.get_hub()
        self.__dict__['_eventlet_listener'] = hub.add(hub.READ,
                                                      self.getsockopt(FD),
                                                      event,
                                                      lambda _: None,
                                                      lambda: None)
        self.__dict__['_eventlet_clock'] = hub.clock

    @_wraps(_Socket.close)
    def close(self, linger=None):
        super().close(linger)
        if self._eventlet_listener is not None:
            eventlet.hubs.get_hub().remove(self._eventlet_listener)
            self.__dict__['_eventlet_listener'] = None
            # wake any blocked threads
            self._eventlet_send_event.wake()
            self._eventlet_recv_event.wake()

    @_wraps(_Socket.getsockopt)
    def getsockopt(self, option):
        result = _Socket_getsockopt(self, option)
        if option == EVENTS:
            # Getting the events causes the zmq socket to process
            # events which may mean a msg can be sent or received. If
            # there is a greenthread blocked and waiting for events,
            # it will miss the edge-triggered read event, so wake it
            # up.
            if (result & POLLOUT):
                self._eventlet_send_event.wake()
            if (result & POLLIN):
                self._eventlet_recv_event.wake()
        return result

    @_wraps(_Socket.send)
    def send(self, msg, flags=0, copy=True, track=False):
        """A send method that's safe to use when multiple greenthreads
        are calling send, send_multipart, recv and recv_multipart on
        the same socket.
        """
        if flags & NOBLOCK:
            result = _Socket_send(self, msg, flags, copy, track)
            # Instead of calling both wake methods, could call
            # self.getsockopt(EVENTS) which would trigger wakeups if
            # needed.
            self._eventlet_send_event.wake()
            self._eventlet_recv_event.wake()
            return result

        # TODO: pyzmq will copy the message buffer and create Message
        # objects under some circumstances. We could do that work here
        # once to avoid doing it every time the send is retried.
        flags |= NOBLOCK
        with self._eventlet_send_lock:
            while True:
                try:
                    return _Socket_send(self, msg, flags, copy, track)
                except ZMQError as e:
                    if e.errno == EAGAIN:
                        self._eventlet_send_event.block()
                    else:
                        raise
                finally:
                    # The call to send processes 0mq events and may
                    # make the socket ready to recv. Wake the next
                    # receiver. (Could check EVENTS for POLLIN here)
                    self._eventlet_recv_event.wake()

    @_wraps(_Socket.send_multipart)
    def send_multipart(self, msg_parts, flags=0, copy=True, track=False):
        """A send_multipart method that's safe to use when multiple
        greenthreads are calling send, send_multipart, recv and
        recv_multipart on the same socket.
        """
        if flags & NOBLOCK:
            return _Socket_send_multipart(self, msg_parts, flags, copy, track)

        # acquire lock here so the subsequent calls to send for the
        # message parts after the first don't block
        with self._eventlet_send_lock:
            return _Socket_send_multipart(self, msg_parts, flags, copy, track)

    @_wraps(_Socket.send_string)
    def send_string(self, u, flags=0, copy=True, encoding='utf-8'):
        """A send_string method that's safe to use when multiple
        greenthreads are calling send, send_string, recv and
        recv_string on the same socket.
        """
        if flags & NOBLOCK:
            return _Socket_send_string(self, u, flags, copy, encoding)

        # acquire lock here so the subsequent calls to send for the
        # message parts after the first don't block
        with self._eventlet_send_lock:
            return _Socket_send_string(self, u, flags, copy, encoding)

    @_wraps(_Socket.send_pyobj)
    def send_pyobj(self, obj, flags=0, protocol=2):
        """A send_pyobj method that's safe to use when multiple
        greenthreads are calling send, send_pyobj, recv and
        recv_pyobj on the same socket.
        """
        if flags & NOBLOCK:
            return _Socket_send_pyobj(self, obj, flags, protocol)

        # acquire lock here so the subsequent calls to send for the
        # message parts after the first don't block
        with self._eventlet_send_lock:
            return _Socket_send_pyobj(self, obj, flags, protocol)

    @_wraps(_Socket.send_json)
    def send_json(self, obj, flags=0, **kwargs):
        """A send_json method that's safe to use when multiple
        greenthreads are calling send, send_json, recv and
        recv_json on the same socket.
        """
        if flags & NOBLOCK:
            return _Socket_send_json(self, obj, flags, **kwargs)

        # acquire lock here so the subsequent calls to send for the
        # message parts after the first don't block
        with self._eventlet_send_lock:
            return _Socket_send_json(self, obj, flags, **kwargs)

    @_wraps(_Socket.recv)
    def recv(self, flags=0, copy=True, track=False):
        """A recv method that's safe to use when multiple greenthreads
        are calling send, send_multipart, recv and recv_multipart on
        the same socket.
        """
        if flags & NOBLOCK:
            msg = _Socket_recv(self, flags, copy, track)
            # Instead of calling both wake methods, could call
            # self.getsockopt(EVENTS) which would trigger wakeups if
            # needed.
            self._eventlet_send_event.wake()
            self._eventlet_recv_event.wake()
            return msg

        deadline = None
        if hasattr(__zmq__, 'RCVTIMEO'):
            sock_timeout = self.getsockopt(__zmq__.RCVTIMEO)
            if sock_timeout == -1:
                pass
            elif sock_timeout > 0:
                deadline = self._eventlet_clock() + sock_timeout / 1000.0
            else:
                raise ValueError(sock_timeout)

        flags |= NOBLOCK
        with self._eventlet_recv_lock:
            while True:
                try:
                    return _Socket_recv(self, flags, copy, track)
                except ZMQError as e:
                    if e.errno == EAGAIN:
                        # zmq in its wisdom decided to reuse EAGAIN for timeouts
                        if deadline is not None and self._eventlet_clock() > deadline:
                            e.is_timeout = True
                            raise

                        self._eventlet_recv_event.block(deadline=deadline)
                    else:
                        raise
                finally:
                    # The call to recv processes 0mq events and may
                    # make the socket ready to send. Wake the next
                    # receiver. (Could check EVENTS for POLLOUT here)
                    self._eventlet_send_event.wake()

    @_wraps(_Socket.recv_multipart)
    def recv_multipart(self, flags=0, copy=True, track=False):
        """A recv_multipart method that's safe to use when multiple
        greenthreads are calling send, send_multipart, recv and
        recv_multipart on the same socket.
        """
        if flags & NOBLOCK:
            return _Socket_recv_multipart(self, flags, copy, track)

        # acquire lock here so the subsequent calls to recv for the
        # message parts after the first don't block
        with self._eventlet_recv_lock:
            return _Socket_recv_multipart(self, flags, copy, track)

    @_wraps(_Socket.recv_string)
    def recv_string(self, flags=0, encoding='utf-8'):
        """A recv_string method that's safe to use when multiple
        greenthreads are calling send, send_string, recv and
        recv_string on the same socket.
        """
        if flags & NOBLOCK:
            return _Socket_recv_string(self, flags, encoding)

        # acquire lock here so the subsequent calls to recv for the
        # message parts after the first don't block
        with self._eventlet_recv_lock:
            return _Socket_recv_string(self, flags, encoding)

    @_wraps(_Socket.recv_json)
    def recv_json(self, flags=0, **kwargs):
        """A recv_json method that's safe to use when multiple
        greenthreads are calling send, send_json, recv and
        recv_json on the same socket.
        """
        if flags & NOBLOCK:
            return _Socket_recv_json(self, flags, **kwargs)

        # acquire lock here so the subsequent calls to recv for the
        # message parts after the first don't block
        with self._eventlet_recv_lock:
            return _Socket_recv_json(self, flags, **kwargs)

    @_wraps(_Socket.recv_pyobj)
    def recv_pyobj(self, flags=0):
        """A recv_pyobj method that's safe to use when multiple
        greenthreads are calling send, send_pyobj, recv and
        recv_pyobj on the same socket.
        """
        if flags & NOBLOCK:
            return _Socket_recv_pyobj(self, flags)

        # acquire lock here so the subsequent calls to recv for the
        # message parts after the first don't block
        with self._eventlet_recv_lock:
            return _Socket_recv_pyobj(self, flags)
