import errno
import sys
from eventlet import patcher, support
from eventlet.hubs import hub
select = patcher.original('select')
time = patcher.original('time')

try:
    BAD_SOCK = {errno.EBADF, errno.WSAENOTSOCK}
except AttributeError:
    BAD_SOCK = {errno.EBADF}


def is_available():
    return hasattr(select, 'select')


class Hub(hub.BaseHub):
    def _remove_bad_fds(self):
        """ Iterate through fds, removing the ones that are bad per the
        operating system.
        """
        all_fds = list(self.listeners[self.READ]) + list(self.listeners[self.WRITE])
        for fd in all_fds:
            try:
                select.select([fd], [], [], 0)
            except OSError as e:
                if support.get_errno(e) in BAD_SOCK:
                    self.remove_descriptor(fd)

    def wait(self, seconds=None):
        readers = self.listeners[self.READ]
        writers = self.listeners[self.WRITE]
        if not readers and not writers:
            if seconds:
                time.sleep(seconds)
            return
        reader_fds = list(readers)
        writer_fds = list(writers)
        all_fds = reader_fds + writer_fds
        try:
            r, w, er = select.select(reader_fds, writer_fds, all_fds, seconds)
        except OSError as e:
            if support.get_errno(e) == errno.EINTR:
                return
            elif support.get_errno(e) in BAD_SOCK:
                self._remove_bad_fds()
                return
            else:
                raise

        for fileno in er:
            readers.get(fileno, hub.noop).cb(fileno)
            writers.get(fileno, hub.noop).cb(fileno)

        for listeners, events in ((readers, r), (writers, w)):
            for fileno in events:
                try:
                    listeners.get(fileno, hub.noop).cb(fileno)
                except self.SYSTEM_EXCEPTIONS:
                    raise
                except:
                    self.squelch_exception(fileno, sys.exc_info())
