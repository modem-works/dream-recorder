import errno
import sys

from eventlet import patcher, support
from eventlet.hubs import hub
select = patcher.original('select')
time = patcher.original('time')


def is_available():
    return hasattr(select, 'poll')


class Hub(hub.BaseHub):
    def __init__(self, clock=None):
        super().__init__(clock)
        self.EXC_MASK = select.POLLERR | select.POLLHUP
        self.READ_MASK = select.POLLIN | select.POLLPRI
        self.WRITE_MASK = select.POLLOUT
        self.poll = select.poll()

    def add(self, evtype, fileno, cb, tb, mac):
        listener = super().add(evtype, fileno, cb, tb, mac)
        self.register(fileno, new=True)
        return listener

    def remove(self, listener):
        super().remove(listener)
        self.register(listener.fileno)

    def register(self, fileno, new=False):
        mask = 0
        if self.listeners[self.READ].get(fileno):
            mask |= self.READ_MASK | self.EXC_MASK
        if self.listeners[self.WRITE].get(fileno):
            mask |= self.WRITE_MASK | self.EXC_MASK
        try:
            if mask:
                if new:
                    self.poll.register(fileno, mask)
                else:
                    try:
                        self.poll.modify(fileno, mask)
                    except OSError:
                        self.poll.register(fileno, mask)
            else:
                try:
                    self.poll.unregister(fileno)
                except (KeyError, OSError):
                    # raised if we try to remove a fileno that was
                    # already removed/invalid
                    pass
        except ValueError:
            # fileno is bad, issue 74
            self.remove_descriptor(fileno)
            raise

    def remove_descriptor(self, fileno):
        super().remove_descriptor(fileno)
        try:
            self.poll.unregister(fileno)
        except (KeyError, ValueError, OSError):
            # raised if we try to remove a fileno that was
            # already removed/invalid
            pass

    def do_poll(self, seconds):
        # poll.poll expects integral milliseconds
        return self.poll.poll(int(seconds * 1000.0))

    def wait(self, seconds=None):
        readers = self.listeners[self.READ]
        writers = self.listeners[self.WRITE]

        if not readers and not writers:
            if seconds:
                time.sleep(seconds)
            return
        try:
            presult = self.do_poll(seconds)
        except OSError as e:
            if support.get_errno(e) == errno.EINTR:
                return
            raise
        SYSTEM_EXCEPTIONS = self.SYSTEM_EXCEPTIONS

        if self.debug_blocking:
            self.block_detect_pre()

        # Accumulate the listeners to call back to prior to
        # triggering any of them. This is to keep the set
        # of callbacks in sync with the events we've just
        # polled for. It prevents one handler from invalidating
        # another.
        callbacks = set()
        noop = hub.noop  # shave getattr
        for fileno, event in presult:
            if event & self.READ_MASK:
                callbacks.add((readers.get(fileno, noop), fileno))
            if event & self.WRITE_MASK:
                callbacks.add((writers.get(fileno, noop), fileno))
            if event & select.POLLNVAL:
                self.remove_descriptor(fileno)
                continue
            if event & self.EXC_MASK:
                callbacks.add((readers.get(fileno, noop), fileno))
                callbacks.add((writers.get(fileno, noop), fileno))

        for listener, fileno in callbacks:
            try:
                listener.cb(fileno)
            except SYSTEM_EXCEPTIONS:
                raise
            except:
                self.squelch_exception(fileno, sys.exc_info())

        if self.debug_blocking:
            self.block_detect_post()
