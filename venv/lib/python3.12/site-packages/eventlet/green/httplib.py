from eventlet import patcher
from eventlet.green import socket

to_patch = [('socket', socket)]

try:
    from eventlet.green import ssl
    to_patch.append(('ssl', ssl))
except ImportError:
    pass

from eventlet.green.http import client
for name in dir(client):
    if name not in patcher.__exclude:
        globals()[name] = getattr(client, name)

if __name__ == '__main__':
    test()
