from eventlet import patcher
from eventlet.green import socket
from eventlet.green import SocketServer

patcher.inject(
    'http.server',
    globals(),
    ('socket', socket),
    ('SocketServer', SocketServer),
    ('socketserver', SocketServer))

del patcher

if __name__ == '__main__':
    test()
