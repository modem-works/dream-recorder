import sys

from eventlet import patcher
from eventlet.green import select

__patched__ = [
    'DefaultSelector',
    'SelectSelector',
]

# We only have green select so the options are:
# * leave it be and have selectors that block
# * try to pretend the "bad" selectors don't exist
# * replace all with SelectSelector for the price of possibly different
#   performance characteristic and missing fileno() method (if someone
#   uses it it'll result in a crash, we may want to implement it in the future)
#
# This module used to follow the third approach but just removing the offending
# selectors is less error prone and less confusing approach.
__deleted__ = [
    'PollSelector',
    'EpollSelector',
    'DevpollSelector',
    'KqueueSelector',
]

patcher.inject('selectors', globals(), ('select', select))

del patcher

if sys.platform != 'win32':
    SelectSelector._select = staticmethod(select.select)

DefaultSelector = SelectSelector
