from py.magic import greenlet

import sys
import types


def emulate():
    module = types.ModuleType('greenlet')
    sys.modules['greenlet'] = module
    module.greenlet = greenlet
    module.getcurrent = greenlet.getcurrent
    module.GreenletExit = greenlet.GreenletExit
