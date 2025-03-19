from eventlet import greenthread

from eventlet.zipkin import api


__original_init__ = greenthread.GreenThread.__init__
__original_main__ = greenthread.GreenThread.main


def _patched__init(self, parent):
    # parent thread saves current TraceData from tls to self
    if api.is_tracing():
        self.trace_data = api.get_trace_data()

    __original_init__(self, parent)


def _patched_main(self, function, args, kwargs):
    # child thread inherits TraceData
    if hasattr(self, 'trace_data'):
        api.set_trace_data(self.trace_data)

    __original_main__(self, function, args, kwargs)


def patch():
    greenthread.GreenThread.__init__ = _patched__init
    greenthread.GreenThread.main = _patched_main


def unpatch():
    greenthread.GreenThread.__init__ = __original_init__
    greenthread.GreenThread.main = __original_main__
