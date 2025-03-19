import sys

if sys.version_info < (3, 12):
    from eventlet import patcher
    from eventlet.green import select
    from eventlet.green import socket
    from eventlet.green import time

    patcher.inject(
        "asyncore",
        globals(),
        ('select', select),
        ('socket', socket),
        ('time', time))

    del patcher
