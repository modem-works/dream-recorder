# @file   dagpool.py
# @author Nat Goodspeed
# @date   2016-08-08
# @brief  Provide DAGPool class

from eventlet.event import Event
from eventlet import greenthread
import collections


# value distinguished from any other Python value including None
_MISSING = object()


class Collision(Exception):
    """
    DAGPool raises Collision when you try to launch two greenthreads with the
    same key, or post() a result for a key corresponding to a greenthread, or
    post() twice for the same key. As with KeyError, str(collision) names the
    key in question.
    """
    pass


class PropagateError(Exception):
    """
    When a DAGPool greenthread terminates with an exception instead of
    returning a result, attempting to retrieve its value raises
    PropagateError.

    Attributes:

    key
        the key of the greenthread which raised the exception

    exc
        the exception object raised by the greenthread
    """
    def __init__(self, key, exc):
        # initialize base class with a reasonable string message
        msg = "PropagateError({}): {}: {}" \
              .format(key, exc.__class__.__name__, exc)
        super().__init__(msg)
        self.msg = msg
        # Unless we set args, this is unpickleable:
        # https://bugs.python.org/issue1692335
        self.args = (key, exc)
        self.key = key
        self.exc = exc

    def __str__(self):
        return self.msg


class DAGPool:
    """
    A DAGPool is a pool that constrains greenthreads, not by max concurrency,
    but by data dependencies.

    This is a way to implement general DAG dependencies. A simple dependency
    tree (flowing in either direction) can straightforwardly be implemented
    using recursion and (e.g.)
    :meth:`GreenThread.imap() <eventlet.greenthread.GreenThread.imap>`.
    What gets complicated is when a given node depends on several other nodes
    as well as contributing to several other nodes.

    With DAGPool, you concurrently launch all applicable greenthreads; each
    will proceed as soon as it has all required inputs. The DAG is implicit in
    which items are required by each greenthread.

    Each greenthread is launched in a DAGPool with a key: any value that can
    serve as a Python dict key. The caller also specifies an iterable of other
    keys on which this greenthread depends. This iterable may be empty.

    The greenthread callable must accept (key, results), where:

    key
        is its own key

    results
        is an iterable of (key, value) pairs.

    A newly-launched DAGPool greenthread is entered immediately, and can
    perform any necessary setup work. At some point it will iterate over the
    (key, value) pairs from the passed 'results' iterable. Doing so blocks the
    greenthread until a value is available for each of the keys specified in
    its initial dependencies iterable. These (key, value) pairs are delivered
    in chronological order, *not* the order in which they are initially
    specified: each value will be delivered as soon as it becomes available.

    The value returned by a DAGPool greenthread becomes the value for its
    key, which unblocks any other greenthreads waiting on that key.

    If a DAGPool greenthread terminates with an exception instead of returning
    a value, attempting to retrieve the value raises :class:`PropagateError`,
    which binds the key of the original greenthread and the original
    exception. Unless the greenthread attempting to retrieve the value handles
    PropagateError, that exception will in turn be wrapped in a PropagateError
    of its own, and so forth. The code that ultimately handles PropagateError
    can follow the chain of PropagateError.exc attributes to discover the flow
    of that exception through the DAG of greenthreads.

    External greenthreads may also interact with a DAGPool. See :meth:`wait_each`,
    :meth:`waitall`, :meth:`post`.

    It is not recommended to constrain external DAGPool producer greenthreads
    in a :class:`GreenPool <eventlet.greenpool.GreenPool>`: it may be hard to
    provably avoid deadlock.

    .. automethod:: __init__
    .. automethod:: __getitem__
    """

    _Coro = collections.namedtuple("_Coro", ("greenthread", "pending"))

    def __init__(self, preload={}):
        """
        DAGPool can be prepopulated with an initial dict or iterable of (key,
        value) pairs. These (key, value) pairs are of course immediately
        available for any greenthread that depends on any of those keys.
        """
        try:
            # If a dict is passed, copy it. Don't risk a subsequent
            # modification to passed dict affecting our internal state.
            iteritems = preload.items()
        except AttributeError:
            # Not a dict, just an iterable of (key, value) pairs
            iteritems = preload

        # Load the initial dict
        self.values = dict(iteritems)

        # track greenthreads
        self.coros = {}

        # The key to blocking greenthreads is the Event.
        self.event = Event()

    def waitall(self):
        """
        waitall() blocks the calling greenthread until there is a value for
        every DAGPool greenthread launched by :meth:`spawn`. It returns a dict
        containing all :class:`preload data <DAGPool>`, all data from
        :meth:`post` and all values returned by spawned greenthreads.

        See also :meth:`wait`.
        """
        # waitall() is an alias for compatibility with GreenPool
        return self.wait()

    def wait(self, keys=_MISSING):
        """
        *keys* is an optional iterable of keys. If you omit the argument, it
        waits for all the keys from :class:`preload data <DAGPool>`, from
        :meth:`post` calls and from :meth:`spawn` calls: in other words, all
        the keys of which this DAGPool is aware.

        wait() blocks the calling greenthread until all of the relevant keys
        have values. wait() returns a dict whose keys are the relevant keys,
        and whose values come from the *preload* data, from values returned by
        DAGPool greenthreads or from :meth:`post` calls.

        If a DAGPool greenthread terminates with an exception, wait() will
        raise :class:`PropagateError` wrapping that exception. If more than
        one greenthread terminates with an exception, it is indeterminate
        which one wait() will raise.

        If an external greenthread posts a :class:`PropagateError` instance,
        wait() will raise that PropagateError. If more than one greenthread
        posts PropagateError, it is indeterminate which one wait() will raise.

        See also :meth:`wait_each_success`, :meth:`wait_each_exception`.
        """
        # This is mostly redundant with wait_each() functionality.
        return dict(self.wait_each(keys))

    def wait_each(self, keys=_MISSING):
        """
        *keys* is an optional iterable of keys. If you omit the argument, it
        waits for all the keys from :class:`preload data <DAGPool>`, from
        :meth:`post` calls and from :meth:`spawn` calls: in other words, all
        the keys of which this DAGPool is aware.

        wait_each() is a generator producing (key, value) pairs as a value
        becomes available for each requested key. wait_each() blocks the
        calling greenthread until the next value becomes available. If the
        DAGPool was prepopulated with values for any of the relevant keys, of
        course those can be delivered immediately without waiting.

        Delivery order is intentionally decoupled from the initial sequence of
        keys: each value is delivered as soon as it becomes available. If
        multiple keys are available at the same time, wait_each() delivers
        each of the ready ones in arbitrary order before blocking again.

        The DAGPool does not distinguish between a value returned by one of
        its own greenthreads and one provided by a :meth:`post` call or *preload* data.

        The wait_each() generator terminates (raises StopIteration) when all
        specified keys have been delivered. Thus, typical usage might be:

        ::

            for key, value in dagpool.wait_each(keys):
                # process this ready key and value
            # continue processing now that we've gotten values for all keys

        By implication, if you pass wait_each() an empty iterable of keys, it
        returns immediately without yielding anything.

        If the value to be delivered is a :class:`PropagateError` exception object, the
        generator raises that PropagateError instead of yielding it.

        See also :meth:`wait_each_success`, :meth:`wait_each_exception`.
        """
        # Build a local set() and then call _wait_each().
        return self._wait_each(self._get_keyset_for_wait_each(keys))

    def wait_each_success(self, keys=_MISSING):
        """
        wait_each_success() filters results so that only success values are
        yielded. In other words, unlike :meth:`wait_each`, wait_each_success()
        will not raise :class:`PropagateError`. Not every provided (or
        defaulted) key will necessarily be represented, though naturally the
        generator will not finish until all have completed.

        In all other respects, wait_each_success() behaves like :meth:`wait_each`.
        """
        for key, value in self._wait_each_raw(self._get_keyset_for_wait_each(keys)):
            if not isinstance(value, PropagateError):
                yield key, value

    def wait_each_exception(self, keys=_MISSING):
        """
        wait_each_exception() filters results so that only exceptions are
        yielded. Not every provided (or defaulted) key will necessarily be
        represented, though naturally the generator will not finish until
        all have completed.

        Unlike other DAGPool methods, wait_each_exception() simply yields
        :class:`PropagateError` instances as values rather than raising them.

        In all other respects, wait_each_exception() behaves like :meth:`wait_each`.
        """
        for key, value in self._wait_each_raw(self._get_keyset_for_wait_each(keys)):
            if isinstance(value, PropagateError):
                yield key, value

    def _get_keyset_for_wait_each(self, keys):
        """
        wait_each(), wait_each_success() and wait_each_exception() promise
        that if you pass an iterable of keys, the method will wait for results
        from those keys -- but if you omit the keys argument, the method will
        wait for results from all known keys. This helper implements that
        distinction, returning a set() of the relevant keys.
        """
        if keys is not _MISSING:
            return set(keys)
        else:
            # keys arg omitted -- use all the keys we know about
            return set(self.coros.keys()) | set(self.values.keys())

    def _wait_each(self, pending):
        """
        When _wait_each() encounters a value of PropagateError, it raises it.

        In all other respects, _wait_each() behaves like _wait_each_raw().
        """
        for key, value in self._wait_each_raw(pending):
            yield key, self._value_or_raise(value)

    @staticmethod
    def _value_or_raise(value):
        # Most methods attempting to deliver PropagateError should raise that
        # instead of simply returning it.
        if isinstance(value, PropagateError):
            raise value
        return value

    def _wait_each_raw(self, pending):
        """
        pending is a set() of keys for which we intend to wait. THIS SET WILL
        BE DESTRUCTIVELY MODIFIED: as each key acquires a value, that key will
        be removed from the passed 'pending' set.

        _wait_each_raw() does not treat a PropagateError instance specially:
        it will be yielded to the caller like any other value.

        In all other respects, _wait_each_raw() behaves like wait_each().
        """
        while True:
            # Before even waiting, show caller any (key, value) pairs that
            # are already available. Copy 'pending' because we want to be able
            # to remove items from the original set while iterating.
            for key in pending.copy():
                value = self.values.get(key, _MISSING)
                if value is not _MISSING:
                    # found one, it's no longer pending
                    pending.remove(key)
                    yield (key, value)

            if not pending:
                # Once we've yielded all the caller's keys, done.
                break

            # There are still more keys pending, so wait.
            self.event.wait()

    def spawn(self, key, depends, function, *args, **kwds):
        """
        Launch the passed *function(key, results, ...)* as a greenthread,
        passing it:

        - the specified *key*
        - an iterable of (key, value) pairs
        - whatever other positional args or keywords you specify.

        Iterating over the *results* iterable behaves like calling
        :meth:`wait_each(depends) <DAGPool.wait_each>`.

        Returning from *function()* behaves like
        :meth:`post(key, return_value) <DAGPool.post>`.

        If *function()* terminates with an exception, that exception is wrapped
        in :class:`PropagateError` with the greenthread's *key* and (effectively) posted
        as the value for that key. Attempting to retrieve that value will
        raise that PropagateError.

        Thus, if the greenthread with key 'a' terminates with an exception,
        and greenthread 'b' depends on 'a', when greenthread 'b' attempts to
        iterate through its *results* argument, it will encounter
        PropagateError. So by default, an uncaught exception will propagate
        through all the downstream dependencies.

        If you pass :meth:`spawn` a key already passed to spawn() or :meth:`post`, spawn()
        raises :class:`Collision`.
        """
        if key in self.coros or key in self.values:
            raise Collision(key)

        # The order is a bit tricky. First construct the set() of keys.
        pending = set(depends)
        # It's important that we pass to _wait_each() the same 'pending' set()
        # that we store in self.coros for this key. The generator-iterator
        # returned by _wait_each() becomes the function's 'results' iterable.
        newcoro = greenthread.spawn(self._wrapper, function, key,
                                    self._wait_each(pending),
                                    *args, **kwds)
        # Also capture the same (!) set in the new _Coro object for this key.
        # We must be able to observe ready keys being removed from the set.
        self.coros[key] = self._Coro(newcoro, pending)

    def _wrapper(self, function, key, results, *args, **kwds):
        """
        This wrapper runs the top-level function in a DAGPool greenthread,
        posting its return value (or PropagateError) to the DAGPool.
        """
        try:
            # call our passed function
            result = function(key, results, *args, **kwds)
        except Exception as err:
            # Wrap any exception it may raise in a PropagateError.
            result = PropagateError(key, err)
        finally:
            # function() has returned (or terminated with an exception). We no
            # longer need to track this greenthread in self.coros. Remove it
            # first so post() won't complain about a running greenthread.
            del self.coros[key]

        try:
            # as advertised, try to post() our return value
            self.post(key, result)
        except Collision:
            # if we've already post()ed a result, oh well
            pass

        # also, in case anyone cares...
        return result

    def spawn_many(self, depends, function, *args, **kwds):
        """
        spawn_many() accepts a single *function* whose parameters are the same
        as for :meth:`spawn`.

        The difference is that spawn_many() accepts a dependency dict
        *depends*. A new greenthread is spawned for each key in the dict. That
        dict key's value should be an iterable of other keys on which this
        greenthread depends.

        If the *depends* dict contains any key already passed to :meth:`spawn`
        or :meth:`post`, spawn_many() raises :class:`Collision`. It is
        indeterminate how many of the other keys in *depends* will have
        successfully spawned greenthreads.
        """
        # Iterate over 'depends' items, relying on self.spawn() not to
        # context-switch so no one can modify 'depends' along the way.
        for key, deps in depends.items():
            self.spawn(key, deps, function, *args, **kwds)

    def kill(self, key):
        """
        Kill the greenthread that was spawned with the specified *key*.

        If no such greenthread was spawned, raise KeyError.
        """
        # let KeyError, if any, propagate
        self.coros[key].greenthread.kill()
        # once killed, remove it
        del self.coros[key]

    def post(self, key, value, replace=False):
        """
        post(key, value) stores the passed *value* for the passed *key*. It
        then causes each greenthread blocked on its results iterable, or on
        :meth:`wait_each(keys) <DAGPool.wait_each>`, to check for new values.
        A waiting greenthread might not literally resume on every single
        post() of a relevant key, but the first post() of a relevant key
        ensures that it will resume eventually, and when it does it will catch
        up with all relevant post() calls.

        Calling post(key, value) when there is a running greenthread with that
        same *key* raises :class:`Collision`. If you must post(key, value) instead of
        letting the greenthread run to completion, you must first call
        :meth:`kill(key) <DAGPool.kill>`.

        The DAGPool implicitly post()s the return value from each of its
        greenthreads. But a greenthread may explicitly post() a value for its
        own key, which will cause its return value to be discarded.

        Calling post(key, value, replace=False) (the default *replace*) when a
        value for that key has already been posted, by any means, raises
        :class:`Collision`.

        Calling post(key, value, replace=True) when a value for that key has
        already been posted, by any means, replaces the previously-stored
        value. However, that may make it complicated to reason about the
        behavior of greenthreads waiting on that key.

        After a post(key, value1) followed by post(key, value2, replace=True),
        it is unspecified which pending :meth:`wait_each([key...]) <DAGPool.wait_each>`
        calls (or greenthreads iterating over *results* involving that key)
        will observe *value1* versus *value2*. It is guaranteed that
        subsequent wait_each([key...]) calls (or greenthreads spawned after
        that point) will observe *value2*.

        A successful call to
        post(key, :class:`PropagateError(key, ExceptionSubclass) <PropagateError>`)
        ensures that any subsequent attempt to retrieve that key's value will
        raise that PropagateError instance.
        """
        # First, check if we're trying to post() to a key with a running
        # greenthread.
        # A DAGPool greenthread is explicitly permitted to post() to its
        # OWN key.
        coro = self.coros.get(key, _MISSING)
        if coro is not _MISSING and coro.greenthread is not greenthread.getcurrent():
            # oh oh, trying to post a value for running greenthread from
            # some other greenthread
            raise Collision(key)

        # Here, either we're posting a value for a key with no greenthread or
        # we're posting from that greenthread itself.

        # Has somebody already post()ed a value for this key?
        # Unless replace == True, this is a problem.
        if key in self.values and not replace:
            raise Collision(key)

        # Either we've never before posted a value for this key, or we're
        # posting with replace == True.

        # update our database
        self.values[key] = value
        # and wake up pending waiters
        self.event.send()
        # The comment in Event.reset() says: "it's better to create a new
        # event rather than reset an old one". Okay, fine. We do want to be
        # able to support new waiters, so create a new Event.
        self.event = Event()

    def __getitem__(self, key):
        """
        __getitem__(key) (aka dagpool[key]) blocks until *key* has a value,
        then delivers that value.
        """
        # This is a degenerate case of wait_each(). Construct a tuple
        # containing only this 'key'. wait_each() will yield exactly one (key,
        # value) pair. Return just its value.
        for _, value in self.wait_each((key,)):
            return value

    def get(self, key, default=None):
        """
        get() returns the value for *key*. If *key* does not yet have a value,
        get() returns *default*.
        """
        return self._value_or_raise(self.values.get(key, default))

    def keys(self):
        """
        Return a snapshot tuple of keys for which we currently have values.
        """
        # Explicitly return a copy rather than an iterator: don't assume our
        # caller will finish iterating before new values are posted.
        return tuple(self.values.keys())

    def items(self):
        """
        Return a snapshot tuple of currently-available (key, value) pairs.
        """
        # Don't assume our caller will finish iterating before new values are
        # posted.
        return tuple((key, self._value_or_raise(value))
                     for key, value in self.values.items())

    def running(self):
        """
        Return number of running DAGPool greenthreads. This includes
        greenthreads blocked while iterating through their *results* iterable,
        that is, greenthreads waiting on values from other keys.
        """
        return len(self.coros)

    def running_keys(self):
        """
        Return keys for running DAGPool greenthreads. This includes
        greenthreads blocked while iterating through their *results* iterable,
        that is, greenthreads waiting on values from other keys.
        """
        # return snapshot; don't assume caller will finish iterating before we
        # next modify self.coros
        return tuple(self.coros.keys())

    def waiting(self):
        """
        Return number of waiting DAGPool greenthreads, that is, greenthreads
        still waiting on values from other keys. This explicitly does *not*
        include external greenthreads waiting on :meth:`wait`,
        :meth:`waitall`, :meth:`wait_each`.
        """
        # n.b. if Event would provide a count of its waiters, we could say
        # something about external greenthreads as well.
        # The logic to determine this count is exactly the same as the general
        # waiting_for() call.
        return len(self.waiting_for())

    # Use _MISSING instead of None as the default 'key' param so we can permit
    # None as a supported key.
    def waiting_for(self, key=_MISSING):
        """
        waiting_for(key) returns a set() of the keys for which the DAGPool
        greenthread spawned with that *key* is still waiting. If you pass a
        *key* for which no greenthread was spawned, waiting_for() raises
        KeyError.

        waiting_for() without argument returns a dict. Its keys are the keys
        of DAGPool greenthreads still waiting on one or more values. In the
        returned dict, the value of each such key is the set of other keys for
        which that greenthread is still waiting.

        This method allows diagnosing a "hung" DAGPool. If certain
        greenthreads are making no progress, it's possible that they are
        waiting on keys for which there is no greenthread and no :meth:`post` data.
        """
        # We may have greenthreads whose 'pending' entry indicates they're
        # waiting on some keys even though values have now been posted for
        # some or all of those keys, because those greenthreads have not yet
        # regained control since values were posted. So make a point of
        # excluding values that are now available.
        available = set(self.values.keys())

        if key is not _MISSING:
            # waiting_for(key) is semantically different than waiting_for().
            # It's just that they both seem to want the same method name.
            coro = self.coros.get(key, _MISSING)
            if coro is _MISSING:
                # Hmm, no running greenthread with this key. But was there
                # EVER a greenthread with this key? If not, let KeyError
                # propagate.
                self.values[key]
                # Oh good, there's a value for this key. Either the
                # greenthread finished, or somebody posted a value. Just say
                # the greenthread isn't waiting for anything.
                return set()
            else:
                # coro is the _Coro for the running greenthread with the
                # specified key.
                return coro.pending - available

        # This is a waiting_for() call, i.e. a general query rather than for a
        # specific key.

        # Start by iterating over (key, coro) pairs in self.coros. Generate
        # (key, pending) pairs in which 'pending' is the set of keys on which
        # the greenthread believes it's waiting, minus the set of keys that
        # are now available. Filter out any pair in which 'pending' is empty,
        # that is, that greenthread will be unblocked next time it resumes.
        # Make a dict from those pairs.
        return {key: pending
                for key, pending in ((key, (coro.pending - available))
                                     for key, coro in self.coros.items())
                if pending}
