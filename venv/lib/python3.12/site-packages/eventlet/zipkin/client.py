import base64
import warnings

from scribe import scribe
from thrift.transport import TTransport, TSocket
from thrift.protocol import TBinaryProtocol

from eventlet import GreenPile


CATEGORY = 'zipkin'


class ZipkinClient:

    def __init__(self, host='127.0.0.1', port=9410):
        """
        :param host: zipkin collector IP address (default '127.0.0.1')
        :param port: zipkin collector port (default 9410)
        """
        self.host = host
        self.port = port
        self.pile = GreenPile(1)
        self._connect()

    def _connect(self):
        socket = TSocket.TSocket(self.host, self.port)
        self.transport = TTransport.TFramedTransport(socket)
        protocol = TBinaryProtocol.TBinaryProtocol(self.transport,
                                                   False, False)
        self.scribe_client = scribe.Client(protocol)
        try:
            self.transport.open()
        except TTransport.TTransportException as e:
            warnings.warn(e.message)

    def _build_message(self, thrift_obj):
        trans = TTransport.TMemoryBuffer()
        protocol = TBinaryProtocol.TBinaryProtocolAccelerated(trans=trans)
        thrift_obj.write(protocol)
        return base64.b64encode(trans.getvalue())

    def send_to_collector(self, span):
        self.pile.spawn(self._send, span)

    def _send(self, span):
        log_entry = scribe.LogEntry(CATEGORY, self._build_message(span))
        try:
            self.scribe_client.Log([log_entry])
        except Exception as e:
            msg = 'ZipkinClient send error %s' % str(e)
            warnings.warn(msg)
            self._connect()

    def close(self):
        self.transport.close()
