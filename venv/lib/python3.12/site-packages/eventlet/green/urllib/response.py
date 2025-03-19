from eventlet import patcher
patcher.inject('urllib.response', globals())
del patcher
