import errno
import sys
from types import FunctionType

import eventlet
from eventlet import greenio
from eventlet import patcher
from eventlet.green import select, threading, time


__patched__ = ['call', 'check_call', 'Popen']
to_patch = [('select', select), ('threading', threading), ('time', time)]

from eventlet.green import selectors
to_patch.append(('selectors', selectors))

patcher.inject('subprocess', globals(), *to_patch)
subprocess_orig = patcher.original("subprocess")
subprocess_imported = sys.modules.get('subprocess', subprocess_orig)
mswindows = sys.platform == "win32"


if getattr(subprocess_orig, 'TimeoutExpired', None) is None:
    # Backported from Python 3.3.
    # https://bitbucket.org/eventlet/eventlet/issue/89
    class TimeoutExpired(Exception):
        """This exception is raised when the timeout expires while waiting for
        a child process.
        """

        def __init__(self, cmd, timeout, output=None):
            self.cmd = cmd
            self.timeout = timeout
            self.output = output

        def __str__(self):
            return ("Command '%s' timed out after %s seconds" %
                    (self.cmd, self.timeout))
else:
    TimeoutExpired = subprocess_imported.TimeoutExpired


# This is the meat of this module, the green version of Popen.
class Popen(subprocess_orig.Popen):
    """eventlet-friendly version of subprocess.Popen"""
    # We do not believe that Windows pipes support non-blocking I/O. At least,
    # the Python file objects stored on our base-class object have no
    # setblocking() method, and the Python fcntl module doesn't exist on
    # Windows. (see eventlet.greenio.set_nonblocking()) As the sole purpose of
    # this __init__() override is to wrap the pipes for eventlet-friendly
    # non-blocking I/O, don't even bother overriding it on Windows.
    if not mswindows:
        def __init__(self, args, bufsize=0, *argss, **kwds):
            self.args = args
            # Forward the call to base-class constructor
            subprocess_orig.Popen.__init__(self, args, 0, *argss, **kwds)
            # Now wrap the pipes, if any. This logic is loosely borrowed from
            # eventlet.processes.Process.run() method.
            for attr in "stdin", "stdout", "stderr":
                pipe = getattr(self, attr)
                if pipe is not None and type(pipe) != greenio.GreenPipe:
                    # https://github.com/eventlet/eventlet/issues/243
                    # AttributeError: '_io.TextIOWrapper' object has no attribute 'mode'
                    mode = getattr(pipe, 'mode', '')
                    if not mode:
                        if pipe.readable():
                            mode += 'r'
                        if pipe.writable():
                            mode += 'w'
                        # ValueError: can't have unbuffered text I/O
                        if bufsize == 0:
                            bufsize = -1
                    wrapped_pipe = greenio.GreenPipe(pipe, mode, bufsize)
                    setattr(self, attr, wrapped_pipe)
        __init__.__doc__ = subprocess_orig.Popen.__init__.__doc__

    def wait(self, timeout=None, check_interval=0.01):
        # Instead of a blocking OS call, this version of wait() uses logic
        # borrowed from the eventlet 0.2 processes.Process.wait() method.
        if timeout is not None:
            endtime = time.time() + timeout
        try:
            while True:
                status = self.poll()
                if status is not None:
                    return status
                if timeout is not None and time.time() > endtime:
                    raise TimeoutExpired(self.args, timeout)
                eventlet.sleep(check_interval)
        except OSError as e:
            if e.errno == errno.ECHILD:
                # no child process, this happens if the child process
                # already died and has been cleaned up
                return -1
            else:
                raise
    wait.__doc__ = subprocess_orig.Popen.wait.__doc__

    if not mswindows:
        # don't want to rewrite the original _communicate() method, we
        # just want a version that uses eventlet.green.select.select()
        # instead of select.select().
        _communicate = FunctionType(
            subprocess_orig.Popen._communicate.__code__,
            globals())
        try:
            _communicate_with_select = FunctionType(
                subprocess_orig.Popen._communicate_with_select.__code__,
                globals())
            _communicate_with_poll = FunctionType(
                subprocess_orig.Popen._communicate_with_poll.__code__,
                globals())
        except AttributeError:
            pass


# Borrow subprocess.call() and check_call(), but patch them so they reference
# OUR Popen class rather than subprocess.Popen.
def patched_function(function):
    new_function = FunctionType(function.__code__, globals())
    new_function.__kwdefaults__ = function.__kwdefaults__
    new_function.__defaults__ = function.__defaults__
    return new_function


call = patched_function(subprocess_orig.call)
check_call = patched_function(subprocess_orig.check_call)
# check_output is Python 2.7+
if hasattr(subprocess_orig, 'check_output'):
    __patched__.append('check_output')
    check_output = patched_function(subprocess_orig.check_output)
del patched_function

# Keep exceptions identity.
# https://github.com/eventlet/eventlet/issues/413
CalledProcessError = subprocess_imported.CalledProcessError
del subprocess_imported
