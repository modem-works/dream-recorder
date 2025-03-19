import eventlet
from eventlet.hubs import get_hub
__select = eventlet.patcher.original('select')
error = __select.error


__patched__ = ['select']
__deleted__ = ['devpoll', 'poll', 'epoll', 'kqueue', 'kevent']


def get_fileno(obj):
    # The purpose of this function is to exactly replicate
    # the behavior of the select module when confronted with
    # abnormal filenos; the details are extensively tested in
    # the stdlib test/test_select.py.
    try:
        f = obj.fileno
    except AttributeError:
        if not isinstance(obj, int):
            raise TypeError("Expected int or long, got %s" % type(obj))
        return obj
    else:
        rv = f()
        if not isinstance(rv, int):
            raise TypeError("Expected int or long, got %s" % type(rv))
        return rv


def select(read_list, write_list, error_list, timeout=None):
    # error checking like this is required by the stdlib unit tests
    if timeout is not None:
        try:
            timeout = float(timeout)
        except ValueError:
            raise TypeError("Expected number for timeout")
    hub = get_hub()
    timers = []
    current = eventlet.getcurrent()
    assert hub.greenlet is not current, 'do not call blocking functions from the mainloop'
    ds = {}
    for r in read_list:
        ds[get_fileno(r)] = {'read': r}
    for w in write_list:
        ds.setdefault(get_fileno(w), {})['write'] = w
    for e in error_list:
        ds.setdefault(get_fileno(e), {})['error'] = e

    listeners = []

    def on_read(d):
        original = ds[get_fileno(d)]['read']
        current.switch(([original], [], []))

    def on_write(d):
        original = ds[get_fileno(d)]['write']
        current.switch(([], [original], []))

    def on_timeout2():
        current.switch(([], [], []))

    def on_timeout():
        # ensure that BaseHub.run() has a chance to call self.wait()
        # at least once before timed out.  otherwise the following code
        # can time out erroneously.
        #
        # s1, s2 = socket.socketpair()
        # print(select.select([], [s1], [], 0))
        timers.append(hub.schedule_call_global(0, on_timeout2))

    if timeout is not None:
        timers.append(hub.schedule_call_global(timeout, on_timeout))
    try:
        for k, v in ds.items():
            if v.get('read'):
                listeners.append(hub.add(hub.READ, k, on_read, current.throw, lambda: None))
            if v.get('write'):
                listeners.append(hub.add(hub.WRITE, k, on_write, current.throw, lambda: None))
        try:
            return hub.switch()
        finally:
            for l in listeners:
                hub.remove(l)
    finally:
        for t in timers:
            t.cancel()
