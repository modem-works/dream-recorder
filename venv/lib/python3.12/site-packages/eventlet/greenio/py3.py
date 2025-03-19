import _pyio as _original_pyio
import errno
import os as _original_os
import socket as _original_socket
from io import (
    BufferedRandom as _OriginalBufferedRandom,
    BufferedReader as _OriginalBufferedReader,
    BufferedWriter as _OriginalBufferedWriter,
    DEFAULT_BUFFER_SIZE,
    TextIOWrapper as _OriginalTextIOWrapper,
    IOBase as _OriginalIOBase,
)
from types import FunctionType

from eventlet.greenio.base import (
    _operation_on_closed_file,
    greenpipe_doc,
    set_nonblocking,
    SOCKET_BLOCKING,
)
from eventlet.hubs import notify_close, notify_opened, IOClosed, trampoline
from eventlet.support import get_errno

__all__ = ['_fileobject', 'GreenPipe']

# TODO get rid of this, it only seems like the original _fileobject
_fileobject = _original_socket.SocketIO

# Large part of the following code is copied from the original
# eventlet.greenio module


class GreenFileIO(_OriginalIOBase):
    def __init__(self, name, mode='r', closefd=True, opener=None):
        if isinstance(name, int):
            fileno = name
            self._name = "<fd:%d>" % fileno
        else:
            assert isinstance(name, str)
            with open(name, mode) as fd:
                self._name = fd.name
                fileno = _original_os.dup(fd.fileno())

        notify_opened(fileno)
        self._fileno = fileno
        self._mode = mode
        self._closed = False
        set_nonblocking(self)
        self._seekable = None

    @property
    def closed(self):
        return self._closed

    def seekable(self):
        if self._seekable is None:
            try:
                _original_os.lseek(self._fileno, 0, _original_os.SEEK_CUR)
            except OSError as e:
                if get_errno(e) == errno.ESPIPE:
                    self._seekable = False
                else:
                    raise
            else:
                self._seekable = True

        return self._seekable

    def readable(self):
        return 'r' in self._mode or '+' in self._mode

    def writable(self):
        return 'w' in self._mode or '+' in self._mode or 'a' in self._mode

    def fileno(self):
        return self._fileno

    def read(self, size=-1):
        if size == -1:
            return self.readall()

        while True:
            try:
                return _original_os.read(self._fileno, size)
            except OSError as e:
                if get_errno(e) not in SOCKET_BLOCKING:
                    raise OSError(*e.args)
                self._trampoline(self, read=True)

    def readall(self):
        buf = []
        while True:
            try:
                chunk = _original_os.read(self._fileno, DEFAULT_BUFFER_SIZE)
                if chunk == b'':
                    return b''.join(buf)
                buf.append(chunk)
            except OSError as e:
                if get_errno(e) not in SOCKET_BLOCKING:
                    raise OSError(*e.args)
                self._trampoline(self, read=True)

    def readinto(self, b):
        up_to = len(b)
        data = self.read(up_to)
        bytes_read = len(data)
        b[:bytes_read] = data
        return bytes_read

    def isatty(self):
        try:
            return _original_os.isatty(self.fileno())
        except OSError as e:
            raise OSError(*e.args)

    def _trampoline(self, fd, read=False, write=False, timeout=None, timeout_exc=None):
        if self._closed:
            # Don't trampoline if we're already closed.
            raise IOClosed()
        try:
            return trampoline(fd, read=read, write=write, timeout=timeout,
                              timeout_exc=timeout_exc,
                              mark_as_closed=self._mark_as_closed)
        except IOClosed:
            # Our fileno has been obsoleted. Defang ourselves to
            # prevent spurious closes.
            self._mark_as_closed()
            raise

    def _mark_as_closed(self):
        """ Mark this socket as being closed """
        self._closed = True

    def write(self, data):
        view = memoryview(data)
        datalen = len(data)
        offset = 0
        while offset < datalen:
            try:
                written = _original_os.write(self._fileno, view[offset:])
            except OSError as e:
                if get_errno(e) not in SOCKET_BLOCKING:
                    raise OSError(*e.args)
                trampoline(self, write=True)
            else:
                offset += written
        return offset

    def close(self):
        if not self._closed:
            self._closed = True
            _original_os.close(self._fileno)
        notify_close(self._fileno)
        for method in [
                'fileno', 'flush', 'isatty', 'next', 'read', 'readinto',
                'readline', 'readlines', 'seek', 'tell', 'truncate',
                'write', 'xreadlines', '__iter__', '__next__', 'writelines']:
            setattr(self, method, _operation_on_closed_file)

    def truncate(self, size=-1):
        if size is None:
            size = -1
        if size == -1:
            size = self.tell()
        try:
            rv = _original_os.ftruncate(self._fileno, size)
        except OSError as e:
            raise OSError(*e.args)
        else:
            self.seek(size)  # move position&clear buffer
            return rv

    def seek(self, offset, whence=_original_os.SEEK_SET):
        try:
            return _original_os.lseek(self._fileno, offset, whence)
        except OSError as e:
            raise OSError(*e.args)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


_open_environment = dict(globals())
_open_environment.update(dict(
    BufferedRandom=_OriginalBufferedRandom,
    BufferedWriter=_OriginalBufferedWriter,
    BufferedReader=_OriginalBufferedReader,
    TextIOWrapper=_OriginalTextIOWrapper,
    FileIO=GreenFileIO,
    os=_original_os,
))
if hasattr(_original_pyio, 'text_encoding'):
    _open_environment['text_encoding'] = _original_pyio.text_encoding

_pyio_open = getattr(_original_pyio.open, '__wrapped__', _original_pyio.open)
_open = FunctionType(
    _pyio_open.__code__,
    _open_environment,
)


def GreenPipe(name, mode="r", buffering=-1, encoding=None, errors=None,
              newline=None, closefd=True, opener=None):
    try:
        fileno = name.fileno()
    except AttributeError:
        pass
    else:
        fileno = _original_os.dup(fileno)
        name.close()
        name = fileno

    return _open(name, mode, buffering, encoding, errors, newline, closefd, opener)


GreenPipe.__doc__ = greenpipe_doc
