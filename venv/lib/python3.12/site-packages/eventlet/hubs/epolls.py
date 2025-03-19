import errno
from eventlet import patcher, support
from eventlet.hubs import hub, poll
select = patcher.original('select')


def is_available():
    return hasattr(select, 'epoll')


# NOTE: we rely on the fact that the epoll flag constants
# are identical in value to the poll constants
class Hub(poll.Hub):
    def __init__(self, clock=None):
        super().__init__(clock=clock)
        self.poll = select.epoll()

    def add(self, evtype, fileno, cb, tb, mac):
        oldlisteners = bool(self.listeners[self.READ].get(fileno) or
                            self.listeners[self.WRITE].get(fileno))
        # not super() to avoid double register()
        listener = hub.BaseHub.add(self, evtype, fileno, cb, tb, mac)
        try:
            self.register(fileno, new=not oldlisteners)
        except OSError as ex:    # ignore EEXIST, #80
            if support.get_errno(ex) != errno.EEXIST:
                raise
        return listener

    def do_poll(self, seconds):
        return self.poll.poll(seconds)
