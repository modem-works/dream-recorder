from code import InteractiveConsole
import errno
import socket
import sys

import eventlet
from eventlet import hubs
from eventlet.support import greenlets, get_errno

try:
    sys.ps1
except AttributeError:
    sys.ps1 = '>>> '
try:
    sys.ps2
except AttributeError:
    sys.ps2 = '... '


class FileProxy:
    def __init__(self, f):
        self.f = f

    def isatty(self):
        return True

    def flush(self):
        pass

    def write(self, data, *a, **kw):
        try:
            self.f.write(data, *a, **kw)
            self.f.flush()
        except OSError as e:
            if get_errno(e) != errno.EPIPE:
                raise

    def readline(self, *a):
        return self.f.readline(*a).replace('\r\n', '\n')

    def __getattr__(self, attr):
        return getattr(self.f, attr)


# @@tavis: the `locals` args below mask the built-in function.  Should
# be renamed.
class SocketConsole(greenlets.greenlet):
    def __init__(self, desc, hostport, locals):
        self.hostport = hostport
        self.locals = locals
        # mangle the socket
        self.desc = FileProxy(desc)
        greenlets.greenlet.__init__(self)

    def run(self):
        try:
            console = InteractiveConsole(self.locals)
            console.interact()
        finally:
            self.switch_out()
            self.finalize()

    def switch(self, *args, **kw):
        self.saved = sys.stdin, sys.stderr, sys.stdout
        sys.stdin = sys.stdout = sys.stderr = self.desc
        greenlets.greenlet.switch(self, *args, **kw)

    def switch_out(self):
        sys.stdin, sys.stderr, sys.stdout = self.saved

    def finalize(self):
        # restore the state of the socket
        self.desc = None
        if len(self.hostport) >= 2:
            host = self.hostport[0]
            port = self.hostport[1]
            print("backdoor closed to %s:%s" % (host, port,))
        else:
            print('backdoor closed')


def backdoor_server(sock, locals=None):
    """ Blocking function that runs a backdoor server on the socket *sock*,
    accepting connections and running backdoor consoles for each client that
    connects.

    The *locals* argument is a dictionary that will be included in the locals()
    of the interpreters.  It can be convenient to stick important application
    variables in here.
    """
    listening_on = sock.getsockname()
    if sock.family == socket.AF_INET:
        # Expand result to IP + port
        listening_on = '%s:%s' % listening_on
    elif sock.family == socket.AF_INET6:
        ip, port, _, _ = listening_on
        listening_on = '%s:%s' % (ip, port,)
    # No action needed if sock.family == socket.AF_UNIX

    print("backdoor server listening on %s" % (listening_on,))
    try:
        while True:
            socketpair = None
            try:
                socketpair = sock.accept()
                backdoor(socketpair, locals)
            except OSError as e:
                # Broken pipe means it was shutdown
                if get_errno(e) != errno.EPIPE:
                    raise
            finally:
                if socketpair:
                    socketpair[0].close()
    finally:
        sock.close()


def backdoor(conn_info, locals=None):
    """Sets up an interactive console on a socket with a single connected
    client.  This does not block the caller, as it spawns a new greenlet to
    handle the console.  This is meant to be called from within an accept loop
    (such as backdoor_server).
    """
    conn, addr = conn_info
    if conn.family == socket.AF_INET:
        host, port = addr
        print("backdoor to %s:%s" % (host, port))
    elif conn.family == socket.AF_INET6:
        host, port, _, _ = addr
        print("backdoor to %s:%s" % (host, port))
    else:
        print('backdoor opened')
    fl = conn.makefile("rw")
    console = SocketConsole(fl, addr, locals)
    hub = hubs.get_hub()
    hub.schedule_call_global(0, console.switch)


if __name__ == '__main__':
    backdoor_server(eventlet.listen(('127.0.0.1', 9000)), {})
