import errno
import os
import socket
import sys
import time
import warnings

import eventlet
from eventlet.hubs import trampoline, notify_opened, IOClosed
from eventlet.support import get_errno

__all__ = [
    'GreenSocket', '_GLOBAL_DEFAULT_TIMEOUT', 'set_nonblocking',
    'SOCKET_BLOCKING', 'SOCKET_CLOSED', 'CONNECT_ERR', 'CONNECT_SUCCESS',
    'shutdown_safe', 'SSL',
    'socket_timeout',
]

BUFFER_SIZE = 4096
CONNECT_ERR = {errno.EINPROGRESS, errno.EALREADY, errno.EWOULDBLOCK}
CONNECT_SUCCESS = {0, errno.EISCONN}
if sys.platform[:3] == "win":
    CONNECT_ERR.add(errno.WSAEINVAL)   # Bug 67

_original_socket = eventlet.patcher.original('socket').socket


if sys.version_info >= (3, 10):
    socket_timeout = socket.timeout  # Really, TimeoutError
else:
    socket_timeout = eventlet.timeout.wrap_is_timeout(socket.timeout)


def socket_connect(descriptor, address):
    """
    Attempts to connect to the address, returns the descriptor if it succeeds,
    returns None if it needs to trampoline, and raises any exceptions.
    """
    err = descriptor.connect_ex(address)
    if err in CONNECT_ERR:
        return None
    if err not in CONNECT_SUCCESS:
        raise OSError(err, errno.errorcode[err])
    return descriptor


def socket_checkerr(descriptor):
    err = descriptor.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
    if err not in CONNECT_SUCCESS:
        raise OSError(err, errno.errorcode[err])


def socket_accept(descriptor):
    """
    Attempts to accept() on the descriptor, returns a client,address tuple
    if it succeeds; returns None if it needs to trampoline, and raises
    any exceptions.
    """
    try:
        return descriptor.accept()
    except OSError as e:
        if get_errno(e) == errno.EWOULDBLOCK:
            return None
        raise


if sys.platform[:3] == "win":
    # winsock sometimes throws ENOTCONN
    SOCKET_BLOCKING = {errno.EAGAIN, errno.EWOULDBLOCK}
    SOCKET_CLOSED = {errno.ECONNRESET, errno.ENOTCONN, errno.ESHUTDOWN}
else:
    # oddly, on linux/darwin, an unconnected socket is expected to block,
    # so we treat ENOTCONN the same as EWOULDBLOCK
    SOCKET_BLOCKING = {errno.EAGAIN, errno.EWOULDBLOCK, errno.ENOTCONN}
    SOCKET_CLOSED = {errno.ECONNRESET, errno.ESHUTDOWN, errno.EPIPE}


def set_nonblocking(fd):
    """
    Sets the descriptor to be nonblocking.  Works on many file-like
    objects as well as sockets.  Only sockets can be nonblocking on
    Windows, however.
    """
    try:
        setblocking = fd.setblocking
    except AttributeError:
        # fd has no setblocking() method. It could be that this version of
        # Python predates socket.setblocking(). In that case, we can still set
        # the flag "by hand" on the underlying OS fileno using the fcntl
        # module.
        try:
            import fcntl
        except ImportError:
            # Whoops, Windows has no fcntl module. This might not be a socket
            # at all, but rather a file-like object with no setblocking()
            # method. In particular, on Windows, pipes don't support
            # non-blocking I/O and therefore don't have that method. Which
            # means fcntl wouldn't help even if we could load it.
            raise NotImplementedError("set_nonblocking() on a file object "
                                      "with no setblocking() method "
                                      "(Windows pipes don't support non-blocking I/O)")
        # We managed to import fcntl.
        fileno = fd.fileno()
        orig_flags = fcntl.fcntl(fileno, fcntl.F_GETFL)
        new_flags = orig_flags | os.O_NONBLOCK
        if new_flags != orig_flags:
            fcntl.fcntl(fileno, fcntl.F_SETFL, new_flags)
    else:
        # socket supports setblocking()
        setblocking(0)


try:
    from socket import _GLOBAL_DEFAULT_TIMEOUT
except ImportError:
    _GLOBAL_DEFAULT_TIMEOUT = object()


class GreenSocket:
    """
    Green version of socket.socket class, that is intended to be 100%
    API-compatible.

    It also recognizes the keyword parameter, 'set_nonblocking=True'.
    Pass False to indicate that socket is already in non-blocking mode
    to save syscalls.
    """

    # This placeholder is to prevent __getattr__ from creating an infinite call loop
    fd = None

    def __init__(self, family=socket.AF_INET, *args, **kwargs):
        should_set_nonblocking = kwargs.pop('set_nonblocking', True)
        if isinstance(family, int):
            fd = _original_socket(family, *args, **kwargs)
            # Notify the hub that this is a newly-opened socket.
            notify_opened(fd.fileno())
        else:
            fd = family

        # import timeout from other socket, if it was there
        try:
            self._timeout = fd.gettimeout() or socket.getdefaulttimeout()
        except AttributeError:
            self._timeout = socket.getdefaulttimeout()

        # Filter fd.fileno() != -1 so that won't call set non-blocking on
        # closed socket
        if should_set_nonblocking and fd.fileno() != -1:
            set_nonblocking(fd)
        self.fd = fd
        # when client calls setblocking(0) or settimeout(0) the socket must
        # act non-blocking
        self.act_non_blocking = False

        # Copy some attributes from underlying real socket.
        # This is the easiest way that i found to fix
        # https://bitbucket.org/eventlet/eventlet/issue/136
        # Only `getsockopt` is required to fix that issue, others
        # are just premature optimization to save __getattr__ call.
        self.bind = fd.bind
        self.close = fd.close
        self.fileno = fd.fileno
        self.getsockname = fd.getsockname
        self.getsockopt = fd.getsockopt
        self.listen = fd.listen
        self.setsockopt = fd.setsockopt
        self.shutdown = fd.shutdown
        self._closed = False

    @property
    def _sock(self):
        return self

    def _get_io_refs(self):
        return self.fd._io_refs

    def _set_io_refs(self, value):
        self.fd._io_refs = value

    _io_refs = property(_get_io_refs, _set_io_refs)

    # Forward unknown attributes to fd, cache the value for future use.
    # I do not see any simple attribute which could be changed
    # so caching everything in self is fine.
    # If we find such attributes - only attributes having __get__ might be cached.
    # For now - I do not want to complicate it.
    def __getattr__(self, name):
        if self.fd is None:
            raise AttributeError(name)
        attr = getattr(self.fd, name)
        setattr(self, name, attr)
        return attr

    def _trampoline(self, fd, read=False, write=False, timeout=None, timeout_exc=None):
        """ We need to trampoline via the event hub.
            We catch any signal back from the hub indicating that the operation we
            were waiting on was associated with a filehandle that's since been
            invalidated.
        """
        if self._closed:
            # If we did any logging, alerting to a second trampoline attempt on a closed
            # socket here would be useful.
            raise IOClosed()
        try:
            return trampoline(fd, read=read, write=write, timeout=timeout,
                              timeout_exc=timeout_exc,
                              mark_as_closed=self._mark_as_closed)
        except IOClosed:
            # This socket's been obsoleted. De-fang it.
            self._mark_as_closed()
            raise

    def accept(self):
        if self.act_non_blocking:
            res = self.fd.accept()
            notify_opened(res[0].fileno())
            return res
        fd = self.fd
        _timeout_exc = socket_timeout('timed out')
        while True:
            res = socket_accept(fd)
            if res is not None:
                client, addr = res
                notify_opened(client.fileno())
                set_nonblocking(client)
                return type(self)(client), addr
            self._trampoline(fd, read=True, timeout=self.gettimeout(), timeout_exc=_timeout_exc)

    def _mark_as_closed(self):
        """ Mark this socket as being closed """
        self._closed = True

    def __del__(self):
        # This is in case self.close is not assigned yet (currently the constructor does it)
        close = getattr(self, 'close', None)
        if close is not None:
            close()

    def connect(self, address):
        if self.act_non_blocking:
            return self.fd.connect(address)
        fd = self.fd
        _timeout_exc = socket_timeout('timed out')
        if self.gettimeout() is None:
            while not socket_connect(fd, address):
                try:
                    self._trampoline(fd, write=True)
                except IOClosed:
                    raise OSError(errno.EBADFD)
                socket_checkerr(fd)
        else:
            end = time.time() + self.gettimeout()
            while True:
                if socket_connect(fd, address):
                    return
                if time.time() >= end:
                    raise _timeout_exc
                timeout = end - time.time()
                try:
                    self._trampoline(fd, write=True, timeout=timeout, timeout_exc=_timeout_exc)
                except IOClosed:
                    # ... we need some workable errno here.
                    raise OSError(errno.EBADFD)
                socket_checkerr(fd)

    def connect_ex(self, address):
        if self.act_non_blocking:
            return self.fd.connect_ex(address)
        fd = self.fd
        if self.gettimeout() is None:
            while not socket_connect(fd, address):
                try:
                    self._trampoline(fd, write=True)
                    socket_checkerr(fd)
                except OSError as ex:
                    return get_errno(ex)
                except IOClosed:
                    return errno.EBADFD
                return 0
        else:
            end = time.time() + self.gettimeout()
            timeout_exc = socket.timeout(errno.EAGAIN)
            while True:
                try:
                    if socket_connect(fd, address):
                        return 0
                    if time.time() >= end:
                        raise timeout_exc
                    self._trampoline(fd, write=True, timeout=end - time.time(),
                                     timeout_exc=timeout_exc)
                    socket_checkerr(fd)
                except OSError as ex:
                    return get_errno(ex)
                except IOClosed:
                    return errno.EBADFD
                return 0

    def dup(self, *args, **kw):
        sock = self.fd.dup(*args, **kw)
        newsock = type(self)(sock, set_nonblocking=False)
        newsock.settimeout(self.gettimeout())
        return newsock

    def makefile(self, *args, **kwargs):
        return _original_socket.makefile(self, *args, **kwargs)

    def makeGreenFile(self, *args, **kw):
        warnings.warn("makeGreenFile has been deprecated, please use "
                      "makefile instead", DeprecationWarning, stacklevel=2)
        return self.makefile(*args, **kw)

    def _read_trampoline(self):
        self._trampoline(
            self.fd,
            read=True,
            timeout=self.gettimeout(),
            timeout_exc=socket_timeout('timed out'))

    def _recv_loop(self, recv_meth, empty_val, *args):
        if self.act_non_blocking:
            return recv_meth(*args)

        while True:
            try:
                # recv: bufsize=0?
                # recv_into: buffer is empty?
                # This is needed because behind the scenes we use sockets in
                # nonblocking mode and builtin recv* methods. Attempting to read
                # 0 bytes from a nonblocking socket using a builtin recv* method
                # does not raise a timeout exception. Since we're simulating
                # a blocking socket here we need to produce a timeout exception
                # if needed, hence the call to trampoline.
                if not args[0]:
                    self._read_trampoline()
                return recv_meth(*args)
            except OSError as e:
                if get_errno(e) in SOCKET_BLOCKING:
                    pass
                elif get_errno(e) in SOCKET_CLOSED:
                    return empty_val
                else:
                    raise

            try:
                self._read_trampoline()
            except IOClosed as e:
                # Perhaps we should return '' instead?
                raise EOFError()

    def recv(self, bufsize, flags=0):
        return self._recv_loop(self.fd.recv, b'', bufsize, flags)

    def recvfrom(self, bufsize, flags=0):
        return self._recv_loop(self.fd.recvfrom, b'', bufsize, flags)

    def recv_into(self, buffer, nbytes=0, flags=0):
        return self._recv_loop(self.fd.recv_into, 0, buffer, nbytes, flags)

    def recvfrom_into(self, buffer, nbytes=0, flags=0):
        return self._recv_loop(self.fd.recvfrom_into, 0, buffer, nbytes, flags)

    def _send_loop(self, send_method, data, *args):
        if self.act_non_blocking:
            return send_method(data, *args)

        _timeout_exc = socket_timeout('timed out')
        while True:
            try:
                return send_method(data, *args)
            except OSError as e:
                eno = get_errno(e)
                if eno == errno.ENOTCONN or eno not in SOCKET_BLOCKING:
                    raise

            try:
                self._trampoline(self.fd, write=True, timeout=self.gettimeout(),
                                 timeout_exc=_timeout_exc)
            except IOClosed:
                raise OSError(errno.ECONNRESET, 'Connection closed by another thread')

    def send(self, data, flags=0):
        return self._send_loop(self.fd.send, data, flags)

    def sendto(self, data, *args):
        return self._send_loop(self.fd.sendto, data, *args)

    def sendall(self, data, flags=0):
        tail = self.send(data, flags)
        len_data = len(data)
        while tail < len_data:
            tail += self.send(data[tail:], flags)

    def setblocking(self, flag):
        if flag:
            self.act_non_blocking = False
            self._timeout = None
        else:
            self.act_non_blocking = True
            self._timeout = 0.0

    def settimeout(self, howlong):
        if howlong is None or howlong == _GLOBAL_DEFAULT_TIMEOUT:
            self.setblocking(True)
            return
        try:
            f = howlong.__float__
        except AttributeError:
            raise TypeError('a float is required')
        howlong = f()
        if howlong < 0.0:
            raise ValueError('Timeout value out of range')
        if howlong == 0.0:
            self.act_non_blocking = True
            self._timeout = 0.0
        else:
            self.act_non_blocking = False
            self._timeout = howlong

    def gettimeout(self):
        return self._timeout

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    if "__pypy__" in sys.builtin_module_names:
        def _reuse(self):
            getattr(self.fd, '_sock', self.fd)._reuse()

        def _drop(self):
            getattr(self.fd, '_sock', self.fd)._drop()


def _operation_on_closed_file(*args, **kwargs):
    raise ValueError("I/O operation on closed file")


greenpipe_doc = """
    GreenPipe is a cooperative replacement for file class.
    It will cooperate on pipes. It will block on regular file.
    Differences from file class:
    - mode is r/w property. Should re r/o
    - encoding property not implemented
    - write/writelines will not raise TypeError exception when non-string data is written
      it will write str(data) instead
    - Universal new lines are not supported and newlines property not implementeded
    - file argument can be descriptor, file name or file object.
    """

# import SSL module here so we can refer to greenio.SSL.exceptionclass
try:
    from OpenSSL import SSL
except ImportError:
    # pyOpenSSL not installed, define exceptions anyway for convenience
    class SSL:
        class WantWriteError(Exception):
            pass

        class WantReadError(Exception):
            pass

        class ZeroReturnError(Exception):
            pass

        class SysCallError(Exception):
            pass


def shutdown_safe(sock):
    """Shuts down the socket. This is a convenience method for
    code that wants to gracefully handle regular sockets, SSL.Connection
    sockets from PyOpenSSL and ssl.SSLSocket objects from Python 2.7 interchangeably.
    Both types of ssl socket require a shutdown() before close,
    but they have different arity on their shutdown method.

    Regular sockets don't need a shutdown before close, but it doesn't hurt.
    """
    try:
        try:
            # socket, ssl.SSLSocket
            return sock.shutdown(socket.SHUT_RDWR)
        except TypeError:
            # SSL.Connection
            return sock.shutdown()
    except OSError as e:
        # we don't care if the socket is already closed;
        # this will often be the case in an http server context
        if get_errno(e) not in (errno.ENOTCONN, errno.EBADF, errno.ENOTSOCK):
            raise
