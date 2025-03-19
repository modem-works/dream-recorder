import os
import sys
import time
import struct
import socket
import random

from eventlet.green import threading
from eventlet.zipkin._thrift.zipkinCore import ttypes
from eventlet.zipkin._thrift.zipkinCore.constants import SERVER_SEND


client = None
_tls = threading.local()  # thread local storage


def put_annotation(msg, endpoint=None):
    """ This is annotation API.
    You can add your own annotation from in your code.
    Annotation is recorded with timestamp automatically.
    e.g.) put_annotation('cache hit for %s' % request)

    :param msg: String message
    :param endpoint: host info
    """
    if is_sample():
        a = ZipkinDataBuilder.build_annotation(msg, endpoint)
        trace_data = get_trace_data()
        trace_data.add_annotation(a)


def put_key_value(key, value, endpoint=None):
    """ This is binary annotation API.
    You can add your own key-value extra information from in your code.
    Key-value doesn't have a time component.
    e.g.) put_key_value('http.uri', '/hoge/index.html')

    :param key: String
    :param value: String
    :param endpoint: host info
    """
    if is_sample():
        b = ZipkinDataBuilder.build_binary_annotation(key, value, endpoint)
        trace_data = get_trace_data()
        trace_data.add_binary_annotation(b)


def is_tracing():
    """ Return whether the current thread is tracking or not """
    return hasattr(_tls, 'trace_data')


def is_sample():
    """ Return whether it should record trace information
        for the request or not
    """
    return is_tracing() and _tls.trace_data.sampled


def get_trace_data():
    if is_tracing():
        return _tls.trace_data


def set_trace_data(trace_data):
    _tls.trace_data = trace_data


def init_trace_data():
    if is_tracing():
        del _tls.trace_data


def _uniq_id():
    """
    Create a random 64-bit signed integer appropriate
    for use as trace and span IDs.
    XXX: By experimentation zipkin has trouble recording traces with ids
    larger than (2 ** 56) - 1
    """
    return random.randint(0, (2 ** 56) - 1)


def generate_trace_id():
    return _uniq_id()


def generate_span_id():
    return _uniq_id()


class TraceData:

    END_ANNOTATION = SERVER_SEND

    def __init__(self, name, trace_id, span_id, parent_id, sampled, endpoint):
        """
        :param name: RPC name (String)
        :param trace_id: int
        :param span_id: int
        :param parent_id: int or None
        :param sampled: lets the downstream servers know
                    if I should record trace data for the request (bool)
        :param endpoint: zipkin._thrift.zipkinCore.ttypes.EndPoint
        """
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_id = parent_id
        self.sampled = sampled
        self.endpoint = endpoint
        self.annotations = []
        self.bannotations = []
        self._done = False

    def add_annotation(self, annotation):
        if annotation.host is None:
            annotation.host = self.endpoint
        if not self._done:
            self.annotations.append(annotation)
            if annotation.value == self.END_ANNOTATION:
                self.flush()

    def add_binary_annotation(self, bannotation):
        if bannotation.host is None:
            bannotation.host = self.endpoint
        if not self._done:
            self.bannotations.append(bannotation)

    def flush(self):
        span = ZipkinDataBuilder.build_span(name=self.name,
                                            trace_id=self.trace_id,
                                            span_id=self.span_id,
                                            parent_id=self.parent_id,
                                            annotations=self.annotations,
                                            bannotations=self.bannotations)
        client.send_to_collector(span)
        self.annotations = []
        self.bannotations = []
        self._done = True


class ZipkinDataBuilder:
    @staticmethod
    def build_span(name, trace_id, span_id, parent_id,
                   annotations, bannotations):
        return ttypes.Span(
            name=name,
            trace_id=trace_id,
            id=span_id,
            parent_id=parent_id,
            annotations=annotations,
            binary_annotations=bannotations
        )

    @staticmethod
    def build_annotation(value, endpoint=None):
        if isinstance(value, str):
            value = value.encode('utf-8')
        assert isinstance(value, bytes)
        return ttypes.Annotation(time.time() * 1000 * 1000,
                                 value, endpoint)

    @staticmethod
    def build_binary_annotation(key, value, endpoint=None):
        annotation_type = ttypes.AnnotationType.STRING
        return ttypes.BinaryAnnotation(key, value, annotation_type, endpoint)

    @staticmethod
    def build_endpoint(ipv4=None, port=None, service_name=None):
        if ipv4 is not None:
            ipv4 = ZipkinDataBuilder._ipv4_to_int(ipv4)
        if service_name is None:
            service_name = ZipkinDataBuilder._get_script_name()
        return ttypes.Endpoint(
            ipv4=ipv4,
            port=port,
            service_name=service_name
        )

    @staticmethod
    def _ipv4_to_int(ipv4):
        return struct.unpack('!i', socket.inet_aton(ipv4))[0]

    @staticmethod
    def _get_script_name():
        return os.path.basename(sys.argv[0])
