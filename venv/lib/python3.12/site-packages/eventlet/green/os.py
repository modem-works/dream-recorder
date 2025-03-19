os_orig = __import__("os")
import errno
socket = __import__("socket")

from eventlet import greenio
from eventlet.support import get_errno
from eventlet import greenthread
from eventlet import hubs
from eventlet.patcher import slurp_properties

__all__ = os_orig.__all__
__patched__ = ['fdopen', 'read', 'write', 'wait', 'waitpid', 'open']

slurp_properties(
    os_orig,
    globals(),
    ignore=__patched__,
    srckeys=dir(os_orig))


def fdopen(fd, *args, **kw):
    """fdopen(fd [, mode='r' [, bufsize]]) -> file_object

    Return an open file object connected to a file descriptor."""
    if not isinstance(fd, int):
        raise TypeError('fd should be int, not %r' % fd)
    try:
        return greenio.GreenPipe(fd, *args, **kw)
    except OSError as e:
        raise OSError(*e.args)


__original_read__ = os_orig.read


def read(fd, n):
    """read(fd, buffersize) -> string

    Read a file descriptor."""
    while True:
        try:
            return __original_read__(fd, n)
        except OSError as e:
            if get_errno(e) == errno.EPIPE:
                return ''
            if get_errno(e) != errno.EAGAIN:
                raise
        try:
            hubs.trampoline(fd, read=True)
        except hubs.IOClosed:
            return ''


__original_write__ = os_orig.write


def write(fd, st):
    """write(fd, string) -> byteswritten

    Write a string to a file descriptor.
    """
    while True:
        try:
            return __original_write__(fd, st)
        except OSError as e:
            if get_errno(e) not in [errno.EAGAIN, errno.EPIPE]:
                raise
        hubs.trampoline(fd, write=True)


def wait():
    """wait() -> (pid, status)

    Wait for completion of a child process."""
    return waitpid(0, 0)


__original_waitpid__ = os_orig.waitpid


def waitpid(pid, options):
    """waitpid(...)
    waitpid(pid, options) -> (pid, status)

    Wait for completion of a given child process."""
    if options & os_orig.WNOHANG != 0:
        return __original_waitpid__(pid, options)
    else:
        new_options = options | os_orig.WNOHANG
        while True:
            rpid, status = __original_waitpid__(pid, new_options)
            if rpid and status >= 0:
                return rpid, status
            greenthread.sleep(0.01)


__original_open__ = os_orig.open


def open(file, flags, mode=0o777, dir_fd=None):
    """ Wrap os.open
        This behaves identically, but collaborates with
        the hub's notify_opened protocol.
    """
    # pathlib workaround #534 pathlib._NormalAccessor wraps `open` in
    # `staticmethod` for py < 3.7 but not 3.7. That means we get here with
    # `file` being a pathlib._NormalAccessor object, and the other arguments
    # shifted.  Fortunately pathlib doesn't use the `dir_fd` argument, so we
    # have space in the parameter list. We use some heuristics to detect this
    # and adjust the parameters (without importing pathlib)
    if type(file).__name__ == '_NormalAccessor':
        file, flags, mode, dir_fd = flags, mode, dir_fd, None

    if dir_fd is not None:
        fd = __original_open__(file, flags, mode, dir_fd=dir_fd)
    else:
        fd = __original_open__(file, flags, mode)
    hubs.notify_opened(fd)
    return fd
