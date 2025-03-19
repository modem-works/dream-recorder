import os
import sys
import warnings


from eventlet import convenience
from eventlet import event
from eventlet import greenpool
from eventlet import greenthread
from eventlet import patcher
from eventlet import queue
from eventlet import semaphore
from eventlet import support
from eventlet import timeout
# NOTE(hberaud): Versions are now managed by hatch and control version.
# hatch has a build hook which generates the version file, however,
# if the project is installed in editable mode then the _version.py file
# will not be updated unless the package is reinstalled (or locally rebuilt).
# For further details, please read:
# https://github.com/ofek/hatch-vcs#build-hook
# https://github.com/maresb/hatch-vcs-footgun-example
try:
    from eventlet._version import __version__
except ImportError:
    __version__ = "0.0.0"
import greenlet

# Force monotonic library search as early as possible.
# Helpful when CPython < 3.5 on Linux blocked in `os.waitpid(-1)` before first use of hub.
# Example: gunicorn
# https://github.com/eventlet/eventlet/issues/401#issuecomment-327500352
try:
    import monotonic
    del monotonic
except ImportError:
    pass

connect = convenience.connect
listen = convenience.listen
serve = convenience.serve
StopServe = convenience.StopServe
wrap_ssl = convenience.wrap_ssl

Event = event.Event

GreenPool = greenpool.GreenPool
GreenPile = greenpool.GreenPile

sleep = greenthread.sleep
spawn = greenthread.spawn
spawn_n = greenthread.spawn_n
spawn_after = greenthread.spawn_after
kill = greenthread.kill

import_patched = patcher.import_patched
monkey_patch = patcher.monkey_patch

Queue = queue.Queue

Semaphore = semaphore.Semaphore
CappedSemaphore = semaphore.CappedSemaphore
BoundedSemaphore = semaphore.BoundedSemaphore

Timeout = timeout.Timeout
with_timeout = timeout.with_timeout
wrap_is_timeout = timeout.wrap_is_timeout
is_timeout = timeout.is_timeout

getcurrent = greenlet.greenlet.getcurrent

# deprecated
TimeoutError, exc_after, call_after_global = (
    support.wrap_deprecated(old, new)(fun) for old, new, fun in (
        ('TimeoutError', 'Timeout', Timeout),
        ('exc_after', 'greenthread.exc_after', greenthread.exc_after),
        ('call_after_global', 'greenthread.call_after_global', greenthread.call_after_global),
    ))

os
