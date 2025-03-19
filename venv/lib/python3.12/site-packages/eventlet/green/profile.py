# Copyright (c) 2010, CCP Games
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of CCP Games nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY CCP GAMES ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CCP GAMES BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""This module is API-equivalent to the standard library :mod:`profile` module
lbut it is greenthread-aware as well as thread-aware.  Use this module
to profile Eventlet-based applications in preference to either :mod:`profile` or :mod:`cProfile`.
FIXME: No testcases for this module.
"""

profile_orig = __import__('profile')
__all__ = profile_orig.__all__

from eventlet.patcher import slurp_properties
slurp_properties(profile_orig, globals(), srckeys=dir(profile_orig))

import sys
import functools

from eventlet import greenthread
from eventlet import patcher
import _thread

thread = patcher.original(_thread.__name__)  # non-monkeypatched module needed


# This class provides the start() and stop() functions
class Profile(profile_orig.Profile):
    base = profile_orig.Profile

    def __init__(self, timer=None, bias=None):
        self.current_tasklet = greenthread.getcurrent()
        self.thread_id = thread.get_ident()
        self.base.__init__(self, timer, bias)
        self.sleeping = {}

    def __call__(self, *args):
        """make callable, allowing an instance to be the profiler"""
        self.dispatcher(*args)

    def _setup(self):
        self._has_setup = True
        self.cur = None
        self.timings = {}
        self.current_tasklet = greenthread.getcurrent()
        self.thread_id = thread.get_ident()
        self.simulate_call("profiler")

    def start(self, name="start"):
        if getattr(self, "running", False):
            return
        self._setup()
        self.simulate_call("start")
        self.running = True
        sys.setprofile(self.dispatcher)

    def stop(self):
        sys.setprofile(None)
        self.running = False
        self.TallyTimings()

    # special cases for the original run commands, makin sure to
    # clear the timer context.
    def runctx(self, cmd, globals, locals):
        if not getattr(self, "_has_setup", False):
            self._setup()
        try:
            return profile_orig.Profile.runctx(self, cmd, globals, locals)
        finally:
            self.TallyTimings()

    def runcall(self, func, *args, **kw):
        if not getattr(self, "_has_setup", False):
            self._setup()
        try:
            return profile_orig.Profile.runcall(self, func, *args, **kw)
        finally:
            self.TallyTimings()

    def trace_dispatch_return_extend_back(self, frame, t):
        """A hack function to override error checking in parent class.  It
        allows invalid returns (where frames weren't preveiously entered into
        the profiler) which can happen for all the tasklets that suddenly start
        to get monitored. This means that the time will eventually be attributed
        to a call high in the chain, when there is a tasklet switch
        """
        if isinstance(self.cur[-2], Profile.fake_frame):
            return False
            self.trace_dispatch_call(frame, 0)
        return self.trace_dispatch_return(frame, t)

    def trace_dispatch_c_return_extend_back(self, frame, t):
        # same for c return
        if isinstance(self.cur[-2], Profile.fake_frame):
            return False  # ignore bogus returns
            self.trace_dispatch_c_call(frame, 0)
        return self.trace_dispatch_return(frame, t)

    def SwitchTasklet(self, t0, t1, t):
        # tally the time spent in the old tasklet
        pt, it, et, fn, frame, rcur = self.cur
        cur = (pt, it + t, et, fn, frame, rcur)

        # we are switching to a new tasklet, store the old
        self.sleeping[t0] = cur, self.timings
        self.current_tasklet = t1

        # find the new one
        try:
            self.cur, self.timings = self.sleeping.pop(t1)
        except KeyError:
            self.cur, self.timings = None, {}
            self.simulate_call("profiler")
            self.simulate_call("new_tasklet")

    def TallyTimings(self):
        oldtimings = self.sleeping
        self.sleeping = {}

        # first, unwind the main "cur"
        self.cur = self.Unwind(self.cur, self.timings)

        # we must keep the timings dicts separate for each tasklet, since it contains
        # the 'ns' item, recursion count of each function in that tasklet.  This is
        # used in the Unwind dude.
        for tasklet, (cur, timings) in oldtimings.items():
            self.Unwind(cur, timings)

            for k, v in timings.items():
                if k not in self.timings:
                    self.timings[k] = v
                else:
                    # accumulate all to the self.timings
                    cc, ns, tt, ct, callers = self.timings[k]
                    # ns should be 0 after unwinding
                    cc += v[0]
                    tt += v[2]
                    ct += v[3]
                    for k1, v1 in v[4].items():
                        callers[k1] = callers.get(k1, 0) + v1
                    self.timings[k] = cc, ns, tt, ct, callers

    def Unwind(self, cur, timings):
        "A function to unwind a 'cur' frame and tally the results"
        "see profile.trace_dispatch_return() for details"
        # also see simulate_cmd_complete()
        while(cur[-1]):
            rpt, rit, ret, rfn, frame, rcur = cur
            frame_total = rit + ret

            if rfn in timings:
                cc, ns, tt, ct, callers = timings[rfn]
            else:
                cc, ns, tt, ct, callers = 0, 0, 0, 0, {}

            if not ns:
                ct = ct + frame_total
                cc = cc + 1

            if rcur:
                ppt, pit, pet, pfn, pframe, pcur = rcur
            else:
                pfn = None

            if pfn in callers:
                callers[pfn] = callers[pfn] + 1  # hack: gather more
            elif pfn:
                callers[pfn] = 1

            timings[rfn] = cc, ns - 1, tt + rit, ct, callers

            ppt, pit, pet, pfn, pframe, pcur = rcur
            rcur = ppt, pit + rpt, pet + frame_total, pfn, pframe, pcur
            cur = rcur
        return cur


def ContextWrap(f):
    @functools.wraps(f)
    def ContextWrapper(self, arg, t):
        current = greenthread.getcurrent()
        if current != self.current_tasklet:
            self.SwitchTasklet(self.current_tasklet, current, t)
            t = 0.0  # the time was billed to the previous tasklet
        return f(self, arg, t)
    return ContextWrapper


# Add "return safety" to the dispatchers
Profile.dispatch = dict(profile_orig.Profile.dispatch, **{
    'return': Profile.trace_dispatch_return_extend_back,
    'c_return': Profile.trace_dispatch_c_return_extend_back,
})
# Add automatic tasklet detection to the callbacks.
Profile.dispatch = {k: ContextWrap(v) for k, v in Profile.dispatch.items()}


# run statements shamelessly stolen from profile.py
def run(statement, filename=None, sort=-1):
    """Run statement under profiler optionally saving results in filename

    This function takes a single argument that can be passed to the
    "exec" statement, and an optional file name.  In all cases this
    routine attempts to "exec" its first argument and gather profiling
    statistics from the execution. If no file name is present, then this
    function automatically prints a simple profiling report, sorted by the
    standard name string (file/line/function-name) that is presented in
    each line.
    """
    prof = Profile()
    try:
        prof = prof.run(statement)
    except SystemExit:
        pass
    if filename is not None:
        prof.dump_stats(filename)
    else:
        return prof.print_stats(sort)


def runctx(statement, globals, locals, filename=None):
    """Run statement under profiler, supplying your own globals and locals,
    optionally saving results in filename.

    statement and filename have the same semantics as profile.run
    """
    prof = Profile()
    try:
        prof = prof.runctx(statement, globals, locals)
    except SystemExit:
        pass

    if filename is not None:
        prof.dump_stats(filename)
    else:
        return prof.print_stats()
