from eventlet import patcher
from eventlet.green import BaseHTTPServer
from eventlet.green import SimpleHTTPServer
from eventlet.green import urllib
from eventlet.green import select

test = None  # bind prior to patcher.inject to silence pyflakes warning below
patcher.inject(
    'http.server',
    globals(),
    ('urllib', urllib),
    ('select', select))

del patcher

if __name__ == '__main__':
    test()  # pyflakes false alarm here unless test = None above
