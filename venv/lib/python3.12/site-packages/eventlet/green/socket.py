import os
import sys

__import__('eventlet.green._socket_nodns')
__socket = sys.modules['eventlet.green._socket_nodns']

__all__ = __socket.__all__
__patched__ = __socket.__patched__ + [
    'create_connection',
    'getaddrinfo',
    'gethostbyname',
    'gethostbyname_ex',
    'getnameinfo',
]

from eventlet.patcher import slurp_properties
slurp_properties(__socket, globals(), srckeys=dir(__socket))


if os.environ.get("EVENTLET_NO_GREENDNS", '').lower() != 'yes':
    from eventlet.support import greendns
    gethostbyname = greendns.gethostbyname
    getaddrinfo = greendns.getaddrinfo
    gethostbyname_ex = greendns.gethostbyname_ex
    getnameinfo = greendns.getnameinfo
    del greendns


def create_connection(address,
                      timeout=_GLOBAL_DEFAULT_TIMEOUT,
                      source_address=None):
    """Connect to *address* and return the socket object.

    Convenience function.  Connect to *address* (a 2-tuple ``(host,
    port)``) and return the socket object.  Passing the optional
    *timeout* parameter will set the timeout on the socket instance
    before attempting to connect.  If no *timeout* is supplied, the
    global default timeout setting returned by :func:`getdefaulttimeout`
    is used.
    """

    err = "getaddrinfo returns an empty list"
    host, port = address
    for res in getaddrinfo(host, port, 0, SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        sock = None
        try:
            sock = socket(af, socktype, proto)
            if timeout is not _GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            sock.connect(sa)
            return sock

        except error as e:
            err = e
            if sock is not None:
                sock.close()

    if not isinstance(err, error):
        err = error(err)
    raise err
