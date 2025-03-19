from eventlet import hubs
from eventlet.semaphore import Semaphore


class Lock(Semaphore):

    """A lock.
    This is API-compatible with :class:`threading.Lock`.

    It is a context manager, and thus can be used in a with block::

      lock = Lock()
      with lock:
        do_some_stuff()
    """

    def release(self, blocking=True):
        """Modify behaviour vs :class:`Semaphore` to raise a RuntimeError
        exception if the value is greater than zero. This corrects behaviour
        to realign with :class:`threading.Lock`.
        """
        if self.counter > 0:
            raise RuntimeError("release unlocked lock")

        # Consciously *do not* call super().release(), but instead inline
        # Semaphore.release() here. We've seen issues with logging._lock
        # deadlocking because garbage collection happened to run mid-release
        # and eliminating the extra stack frame should help prevent that.
        # See https://github.com/eventlet/eventlet/issues/742
        self.counter += 1
        if self._waiters:
            hubs.get_hub().schedule_call_global(0, self._do_acquire)
        return True

    def _at_fork_reinit(self):
        self.counter = 1
        self._waiters.clear()
