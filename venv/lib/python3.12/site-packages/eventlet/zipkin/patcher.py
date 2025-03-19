from eventlet.zipkin import http
from eventlet.zipkin import wsgi
from eventlet.zipkin import greenthread
from eventlet.zipkin import log
from eventlet.zipkin import api
from eventlet.zipkin.client import ZipkinClient


def enable_trace_patch(host='127.0.0.1', port=9410,
                       trace_app_log=False, sampling_rate=1.0):
    """ Apply monkey patch to trace your WSGI application.

    :param host: Scribe daemon IP address (default: '127.0.0.1')
    :param port: Scribe daemon port (default: 9410)
    :param trace_app_log: A Boolean indicating if the tracer will trace
        application log together or not. This facility assume that
        your application uses python standard logging library.
        (default: False)
    :param sampling_rate: A Float value (0.0~1.0) that indicates
        the tracing frequency. If you specify 1.0, all request
        are traced (and sent to Zipkin collecotr).
        If you specify 0.1, only 1/10 requests are traced. (default: 1.0)
    """
    api.client = ZipkinClient(host, port)

    # monkey patch for adding tracing facility
    wsgi.patch(sampling_rate)
    http.patch()
    greenthread.patch()

    # monkey patch for capturing application log
    if trace_app_log:
        log.patch()


def disable_trace_patch():
    http.unpatch()
    wsgi.unpatch()
    greenthread.unpatch()
    log.unpatch()
    api.client.close()
