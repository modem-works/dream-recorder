import random

from eventlet import wsgi
from eventlet.zipkin import api
from eventlet.zipkin._thrift.zipkinCore.constants import \
    SERVER_RECV, SERVER_SEND
from eventlet.zipkin.http import \
    HDR_TRACE_ID, HDR_SPAN_ID, HDR_PARENT_SPAN_ID, HDR_SAMPLED


_sampler = None
__original_handle_one_response__ = wsgi.HttpProtocol.handle_one_response


def _patched_handle_one_response(self):
    api.init_trace_data()
    trace_id = int_or_none(self.headers.getheader(HDR_TRACE_ID))
    span_id = int_or_none(self.headers.getheader(HDR_SPAN_ID))
    parent_id = int_or_none(self.headers.getheader(HDR_PARENT_SPAN_ID))
    sampled = bool_or_none(self.headers.getheader(HDR_SAMPLED))
    if trace_id is None:  # front-end server
        trace_id = span_id = api.generate_trace_id()
        parent_id = None
        sampled = _sampler.sampling()
    ip, port = self.request.getsockname()[:2]
    ep = api.ZipkinDataBuilder.build_endpoint(ip, port)
    trace_data = api.TraceData(name=self.command,
                               trace_id=trace_id,
                               span_id=span_id,
                               parent_id=parent_id,
                               sampled=sampled,
                               endpoint=ep)
    api.set_trace_data(trace_data)
    api.put_annotation(SERVER_RECV)
    api.put_key_value('http.uri', self.path)

    __original_handle_one_response__(self)

    if api.is_sample():
        api.put_annotation(SERVER_SEND)


class Sampler:
    def __init__(self, sampling_rate):
        self.sampling_rate = sampling_rate

    def sampling(self):
        # avoid generating unneeded random numbers
        if self.sampling_rate == 1.0:
            return True
        r = random.random()
        if r < self.sampling_rate:
            return True
        return False


def int_or_none(val):
    if val is None:
        return None
    return int(val, 16)


def bool_or_none(val):
    if val == '1':
        return True
    if val == '0':
        return False
    return None


def patch(sampling_rate):
    global _sampler
    _sampler = Sampler(sampling_rate)
    wsgi.HttpProtocol.handle_one_response = _patched_handle_one_response


def unpatch():
    wsgi.HttpProtocol.handle_one_response = __original_handle_one_response__
