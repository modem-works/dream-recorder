from eventlet import patcher
from eventlet.green import BaseHTTPServer
from eventlet.green import urllib

patcher.inject(
    'http.server',
    globals(),
    ('urllib', urllib))

del patcher

if __name__ == '__main__':
    test()
