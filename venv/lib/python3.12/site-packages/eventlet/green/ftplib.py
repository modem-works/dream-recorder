from eventlet import patcher

# *NOTE: there might be some funny business with the "SOCKS" module
# if it even still exists
from eventlet.green import socket

patcher.inject('ftplib', globals(), ('socket', socket))

del patcher

# Run test program when run as a script
if __name__ == '__main__':
    test()
