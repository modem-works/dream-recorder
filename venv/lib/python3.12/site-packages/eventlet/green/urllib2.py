from eventlet import patcher
from eventlet.green import ftplib
from eventlet.green import httplib
from eventlet.green import socket
from eventlet.green import ssl
from eventlet.green import time
from eventlet.green import urllib

patcher.inject(
    'urllib2',
    globals(),
    ('httplib', httplib),
    ('socket', socket),
    ('ssl', ssl),
    ('time', time),
    ('urllib', urllib))

FTPHandler.ftp_open = patcher.patch_function(FTPHandler.ftp_open, ('ftplib', ftplib))

del patcher
