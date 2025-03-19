from eventlet import patcher
patcher.inject('urllib.parse', globals())
del patcher
