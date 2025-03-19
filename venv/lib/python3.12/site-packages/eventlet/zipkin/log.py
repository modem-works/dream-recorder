import logging

from eventlet.zipkin import api


__original_handle__ = logging.Logger.handle


def _patched_handle(self, record):
    __original_handle__(self, record)
    api.put_annotation(record.getMessage())


def patch():
    logging.Logger.handle = _patched_handle


def unpatch():
    logging.Logger.handle = __original_handle__
