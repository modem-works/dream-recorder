from eventlet import patcher
from eventlet.green.urllib import response
patcher.inject('urllib.error', globals(), ('urllib.response', response))
del patcher
