from __future__ import annotations
try:
    import _imp as imp
except ImportError:
    import imp
import sys
try:
    # Only for this purpose, it's irrelevant if `os` was already patched.
    # https://github.com/eventlet/eventlet/pull/661
    from os import register_at_fork
except ImportError:
    register_at_fork = None

import eventlet


__all__ = ['inject', 'import_patched', 'monkey_patch', 'is_monkey_patched']

__exclude = {'__builtins__', '__file__', '__name__'}


class SysModulesSaver:
    """Class that captures some subset of the current state of
    sys.modules.  Pass in an iterator of module names to the
    constructor."""

    def __init__(self, module_names=()):
        self._saved = {}
        imp.acquire_lock()
        self.save(*module_names)

    def save(self, *module_names):
        """Saves the named modules to the object."""
        for modname in module_names:
            self._saved[modname] = sys.modules.get(modname, None)

    def restore(self):
        """Restores the modules that the saver knows about into
        sys.modules.
        """
        try:
            for modname, mod in self._saved.items():
                if mod is not None:
                    sys.modules[modname] = mod
                else:
                    try:
                        del sys.modules[modname]
                    except KeyError:
                        pass
        finally:
            imp.release_lock()


def inject(module_name, new_globals, *additional_modules):
    """Base method for "injecting" greened modules into an imported module.  It
    imports the module specified in *module_name*, arranging things so
    that the already-imported modules in *additional_modules* are used when
    *module_name* makes its imports.

    **Note:** This function does not create or change any sys.modules item, so
    if your greened module use code like 'sys.modules["your_module_name"]', you
    need to update sys.modules by yourself.

    *new_globals* is either None or a globals dictionary that gets populated
    with the contents of the *module_name* module.  This is useful when creating
    a "green" version of some other module.

    *additional_modules* should be a collection of two-element tuples, of the
    form (<name>, <module>).  If it's not specified, a default selection of
    name/module pairs is used, which should cover all use cases but may be
    slower because there are inevitably redundant or unnecessary imports.
    """
    patched_name = '__patched_module_' + module_name
    if patched_name in sys.modules:
        # returning already-patched module so as not to destroy existing
        # references to patched modules
        return sys.modules[patched_name]

    if not additional_modules:
        # supply some defaults
        additional_modules = (
            _green_os_modules() +
            _green_select_modules() +
            _green_socket_modules() +
            _green_thread_modules() +
            _green_time_modules())
        # _green_MySQLdb()) # enable this after a short baking-in period

    # after this we are gonna screw with sys.modules, so capture the
    # state of all the modules we're going to mess with, and lock
    saver = SysModulesSaver([name for name, m in additional_modules])
    saver.save(module_name)

    # Cover the target modules so that when you import the module it
    # sees only the patched versions
    for name, mod in additional_modules:
        sys.modules[name] = mod

    # Remove the old module from sys.modules and reimport it while
    # the specified modules are in place
    sys.modules.pop(module_name, None)
    # Also remove sub modules and reimport. Use copy the keys to list
    # because of the pop operations will change the content of sys.modules
    # within th loop
    for imported_module_name in list(sys.modules.keys()):
        if imported_module_name.startswith(module_name + '.'):
            sys.modules.pop(imported_module_name, None)
    try:
        module = __import__(module_name, {}, {}, module_name.split('.')[:-1])

        if new_globals is not None:
            # Update the given globals dictionary with everything from this new module
            for name in dir(module):
                if name not in __exclude:
                    new_globals[name] = getattr(module, name)

        # Keep a reference to the new module to prevent it from dying
        sys.modules[patched_name] = module
    finally:
        saver.restore()  # Put the original modules back

    return module


def import_patched(module_name, *additional_modules, **kw_additional_modules):
    """Imports a module in a way that ensures that the module uses "green"
    versions of the standard library modules, so that everything works
    nonblockingly.

    The only required argument is the name of the module to be imported.
    """
    return inject(
        module_name,
        None,
        *additional_modules + tuple(kw_additional_modules.items()))


def patch_function(func, *additional_modules):
    """Decorator that returns a version of the function that patches
    some modules for the duration of the function call.  This is
    deeply gross and should only be used for functions that import
    network libraries within their function bodies that there is no
    way of getting around."""
    if not additional_modules:
        # supply some defaults
        additional_modules = (
            _green_os_modules() +
            _green_select_modules() +
            _green_socket_modules() +
            _green_thread_modules() +
            _green_time_modules())

    def patched(*args, **kw):
        saver = SysModulesSaver()
        for name, mod in additional_modules:
            saver.save(name)
            sys.modules[name] = mod
        try:
            return func(*args, **kw)
        finally:
            saver.restore()
    return patched


def _original_patch_function(func, *module_names):
    """Kind of the contrapositive of patch_function: decorates a
    function such that when it's called, sys.modules is populated only
    with the unpatched versions of the specified modules.  Unlike
    patch_function, only the names of the modules need be supplied,
    and there are no defaults.  This is a gross hack; tell your kids not
    to import inside function bodies!"""
    def patched(*args, **kw):
        saver = SysModulesSaver(module_names)
        for name in module_names:
            sys.modules[name] = original(name)
        try:
            return func(*args, **kw)
        finally:
            saver.restore()
    return patched


def original(modname):
    """ This returns an unpatched version of a module; this is useful for
    Eventlet itself (i.e. tpool)."""
    # note that it's not necessary to temporarily install unpatched
    # versions of all patchable modules during the import of the
    # module; this is because none of them import each other, except
    # for threading which imports thread
    original_name = '__original_module_' + modname
    if original_name in sys.modules:
        return sys.modules.get(original_name)

    # re-import the "pure" module and store it in the global _originals
    # dict; be sure to restore whatever module had that name already
    saver = SysModulesSaver((modname,))
    sys.modules.pop(modname, None)
    # some rudimentary dependency checking -- fortunately the modules
    # we're working on don't have many dependencies so we can just do
    # some special-casing here
    deps = {'threading': '_thread', 'queue': 'threading'}
    if modname in deps:
        dependency = deps[modname]
        saver.save(dependency)
        sys.modules[dependency] = original(dependency)
    try:
        real_mod = __import__(modname, {}, {}, modname.split('.')[:-1])
        if modname in ('Queue', 'queue') and not hasattr(real_mod, '_threading'):
            # tricky hack: Queue's constructor in <2.7 imports
            # threading on every instantiation; therefore we wrap
            # it so that it always gets the original threading
            real_mod.Queue.__init__ = _original_patch_function(
                real_mod.Queue.__init__,
                'threading')
        # save a reference to the unpatched module so it doesn't get lost
        sys.modules[original_name] = real_mod
    finally:
        saver.restore()

    return sys.modules[original_name]


already_patched = {}


def monkey_patch(**on):
    """Globally patches certain system modules to be greenthread-friendly.

    The keyword arguments afford some control over which modules are patched.
    If no keyword arguments are supplied, all possible modules are patched.
    If keywords are set to True, only the specified modules are patched.  E.g.,
    ``monkey_patch(socket=True, select=True)`` patches only the select and
    socket modules.  Most arguments patch the single module of the same name
    (os, time, select).  The exceptions are socket, which also patches the ssl
    module if present; and thread, which patches thread, threading, and Queue.

    It's safe to call monkey_patch multiple times.
    """

    # Workaround for import cycle observed as following in monotonic
    # RuntimeError: no suitable implementation for this system
    # see https://github.com/eventlet/eventlet/issues/401#issuecomment-325015989
    #
    # Make sure the hub is completely imported before any
    # monkey-patching, or we risk recursion if the process of importing
    # the hub calls into monkey-patched modules.
    eventlet.hubs.get_hub()

    accepted_args = {'os', 'select', 'socket',
                     'thread', 'time', 'psycopg', 'MySQLdb',
                     'builtins', 'subprocess'}
    # To make sure only one of them is passed here
    assert not ('__builtin__' in on and 'builtins' in on)
    try:
        b = on.pop('__builtin__')
    except KeyError:
        pass
    else:
        on['builtins'] = b

    default_on = on.pop("all", None)

    for k in on.keys():
        if k not in accepted_args:
            raise TypeError("monkey_patch() got an unexpected "
                            "keyword argument %r" % k)
    if default_on is None:
        default_on = True not in on.values()
    for modname in accepted_args:
        if modname == 'MySQLdb':
            # MySQLdb is only on when explicitly patched for the moment
            on.setdefault(modname, False)
        if modname == 'builtins':
            on.setdefault(modname, False)
        on.setdefault(modname, default_on)

    if on['thread'] and not already_patched.get('thread'):
        _green_existing_locks()

    modules_to_patch = []
    for name, modules_function in [
        ('os', _green_os_modules),
        ('select', _green_select_modules),
        ('socket', _green_socket_modules),
        ('thread', _green_thread_modules),
        ('time', _green_time_modules),
        ('MySQLdb', _green_MySQLdb),
        ('builtins', _green_builtins),
        ('subprocess', _green_subprocess_modules),
    ]:
        if on[name] and not already_patched.get(name):
            modules_to_patch += modules_function()
            already_patched[name] = True

    if on['psycopg'] and not already_patched.get('psycopg'):
        try:
            from eventlet.support import psycopg2_patcher
            psycopg2_patcher.make_psycopg_green()
            already_patched['psycopg'] = True
        except ImportError:
            # note that if we get an importerror from trying to
            # monkeypatch psycopg, we will continually retry it
            # whenever monkey_patch is called; this should not be a
            # performance problem but it allows is_monkey_patched to
            # tell us whether or not we succeeded
            pass

    _threading = original('threading')
    imp.acquire_lock()
    try:
        for name, mod in modules_to_patch:
            orig_mod = sys.modules.get(name)
            if orig_mod is None:
                orig_mod = __import__(name)
            for attr_name in mod.__patched__:
                patched_attr = getattr(mod, attr_name, None)
                if patched_attr is not None:
                    setattr(orig_mod, attr_name, patched_attr)
            deleted = getattr(mod, '__deleted__', [])
            for attr_name in deleted:
                if hasattr(orig_mod, attr_name):
                    delattr(orig_mod, attr_name)

            # https://github.com/eventlet/eventlet/issues/592
            if name == 'threading' and register_at_fork:
                def fix_threading_active(
                    _global_dict=_threading.current_thread.__globals__,
                    # alias orig_mod as patched to reflect its new state
                    # https://github.com/eventlet/eventlet/pull/661#discussion_r509877481
                    _patched=orig_mod,
                ):
                    _prefork_active = [None]

                    def before_fork():
                        _prefork_active[0] = _global_dict['_active']
                        _global_dict['_active'] = _patched._active

                    def after_fork():
                        _global_dict['_active'] = _prefork_active[0]

                    register_at_fork(
                        before=before_fork,
                        after_in_parent=after_fork)
                fix_threading_active()
    finally:
        imp.release_lock()

    import importlib._bootstrap
    thread = original('_thread')
    # importlib must use real thread locks, not eventlet.Semaphore
    importlib._bootstrap._thread = thread

    # Issue #185: Since Python 3.3, threading.RLock is implemented in C and
    # so call a C function to get the thread identifier, instead of calling
    # threading.get_ident(). Force the Python implementation of RLock which
    # calls threading.get_ident() and so is compatible with eventlet.
    import threading
    threading.RLock = threading._PyRLock

    # Issue #508: Since Python 3.7 queue.SimpleQueue is implemented in C,
    # causing a deadlock.  Replace the C implementation with the Python one.
    import queue
    queue.SimpleQueue = queue._PySimpleQueue


def is_monkey_patched(module):
    """Returns True if the given module is monkeypatched currently, False if
    not.  *module* can be either the module itself or its name.

    Based entirely off the name of the module, so if you import a
    module some other way than with the import keyword (including
    import_patched), this might not be correct about that particular
    module."""
    return module in already_patched or \
        getattr(module, '__name__', None) in already_patched


def _green_existing_locks():
    """Make locks created before monkey-patching safe.

    RLocks rely on a Lock and on Python 2, if an unpatched Lock blocks, it
    blocks the native thread. We need to replace these with green Locks.

    This was originally noticed in the stdlib logging module."""
    import gc
    import os
    import threading
    import eventlet.green.thread
    rlock_type = type(threading.RLock())

    # We're monkey-patching so there can't be any greenlets yet, ergo our thread
    # ID is the only valid owner possible.
    tid = eventlet.green.thread.get_ident()

    # Now, upgrade all instances:
    def upgrade(old_lock):
        return _convert_py3_rlock(old_lock, tid)

    _upgrade_instances(sys.modules, rlock_type, upgrade)

    # Report if there are RLocks we couldn't upgrade. For cases where we're
    # using coverage.py in parent process, and more generally for tests in
    # general, this is difficult to ensure, so just don't complain in that case.
    if "PYTEST_CURRENT_TEST" in os.environ:
        return
    # On older Pythons (< 3.10), gc.get_objects() won't return any RLock
    # instances, so this warning won't get logged on older Pythons. However,
    # it's a useful warning, so we try to do it anyway for the benefit of those
    # users on 3.10 or later.
    gc.collect()
    remaining_rlocks = len({o for o in gc.get_objects() if isinstance(o, rlock_type)})
    if remaining_rlocks:
        import logging
        logger = logging.Logger("eventlet")
        logger.error("{} RLock(s) were not greened,".format(remaining_rlocks) +
                     " to fix this error make sure you run eventlet.monkey_patch() " +
                     "before importing any other modules.")


def _upgrade_instances(container, klass, upgrade, visited=None, old_to_new=None):
    """
    Starting with a Python object, find all instances of ``klass``, following
    references in ``dict`` values, ``list`` items, and attributes.

    Once an object is found, replace all instances with
    ``upgrade(found_object)``, again limited to the criteria above.

    In practice this is used only for ``threading.RLock``, so we can assume
    instances are hashable.
    """
    if visited is None:
        visited = {}  # map id(obj) to obj
    if old_to_new is None:
        old_to_new = {}  # map old klass instance to upgrade(old)

    # Handle circular references:
    visited[id(container)] = container

    def upgrade_or_traverse(obj):
        if id(obj) in visited:
            return None
        if isinstance(obj, klass):
            if obj in old_to_new:
                return old_to_new[obj]
            else:
                new = upgrade(obj)
                old_to_new[obj] = new
                return new
        else:
            _upgrade_instances(obj, klass, upgrade, visited, old_to_new)
            return None

    if isinstance(container, dict):
        for k, v in list(container.items()):
            new = upgrade_or_traverse(v)
            if new is not None:
                container[k] = new
    if isinstance(container, list):
        for i, v in enumerate(container):
            new = upgrade_or_traverse(v)
            if new is not None:
                container[i] = new
    try:
        container_vars = vars(container)
    except TypeError:
        pass
    else:
        # If we get here, we're operating on an object that could
        # be doing strange things. If anything bad happens, error and
        # warn the eventlet user to monkey_patch earlier.
        try:
            for k, v in list(container_vars.items()):
                new = upgrade_or_traverse(v)
                if new is not None:
                    setattr(container, k, new)
        except:
            import logging
            logger = logging.Logger("eventlet")
            logger.exception("An exception was thrown while monkey_patching for eventlet. "
                             "to fix this error make sure you run eventlet.monkey_patch() "
                             "before importing any other modules.", exc_info=True)


def _convert_py3_rlock(old, tid):
    """
    Convert a normal RLock to one implemented in Python.

    This is necessary to make RLocks work with eventlet, but also introduces
    bugs, e.g. https://bugs.python.org/issue13697.  So more of a downgrade,
    really.
    """
    import threading
    from eventlet.green.thread import allocate_lock
    new = threading._PyRLock()
    if not hasattr(new, "_block") or not hasattr(new, "_owner"):
        # These will only fail if Python changes its internal implementation of
        # _PyRLock:
        raise RuntimeError(
            "INTERNAL BUG. Perhaps you are using a major version " +
            "of Python that is unsupported by eventlet? Please file a bug " +
            "at https://github.com/eventlet/eventlet/issues/new")
    new._block = allocate_lock()
    acquired = False
    while old._is_owned():
        old.release()
        new.acquire()
        acquired = True
    if old._is_owned():
        new.acquire()
        acquired = True
    if acquired:
        new._owner = tid
    return new


def _green_os_modules():
    from eventlet.green import os
    return [('os', os)]


def _green_select_modules():
    from eventlet.green import select
    modules = [('select', select)]

    from eventlet.green import selectors
    modules.append(('selectors', selectors))

    return modules


def _green_socket_modules():
    from eventlet.green import socket
    try:
        from eventlet.green import ssl
        return [('socket', socket), ('ssl', ssl)]
    except ImportError:
        return [('socket', socket)]


def _green_subprocess_modules():
    from eventlet.green import subprocess
    return [('subprocess', subprocess)]


def _green_thread_modules():
    from eventlet.green import Queue
    from eventlet.green import thread
    from eventlet.green import threading
    return [('queue', Queue), ('_thread', thread), ('threading', threading)]


def _green_time_modules():
    from eventlet.green import time
    return [('time', time)]


def _green_MySQLdb():
    try:
        from eventlet.green import MySQLdb
        return [('MySQLdb', MySQLdb)]
    except ImportError:
        return []


def _green_builtins():
    try:
        from eventlet.green import builtin
        return [('builtins', builtin)]
    except ImportError:
        return []


def slurp_properties(source, destination, ignore=[], srckeys=None):
    """Copy properties from *source* (assumed to be a module) to
    *destination* (assumed to be a dict).

    *ignore* lists properties that should not be thusly copied.
    *srckeys* is a list of keys to copy, if the source's __all__ is
    untrustworthy.
    """
    if srckeys is None:
        srckeys = source.__all__
    destination.update({
        name: getattr(source, name)
        for name in srckeys
        if not (name.startswith('__') or name in ignore)
    })


if __name__ == "__main__":
    sys.argv.pop(0)
    monkey_patch()
    with open(sys.argv[0]) as f:
        code = compile(f.read(), sys.argv[0], 'exec')
        exec(code)
