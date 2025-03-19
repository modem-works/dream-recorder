# Copyright (c) 2009 Denis Bilenko, denis.bilenko at gmail com
# Copyright (c) 2010 Eventlet Contributors (see AUTHORS)
# and licensed under the MIT license:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Synchronized queues.

The :mod:`eventlet.queue` module implements multi-producer, multi-consumer
queues that work across greenlets, with the API similar to the classes found in
the standard :mod:`Queue` and :class:`multiprocessing <multiprocessing.Queue>`
modules.

A major difference is that queues in this module operate as channels when
initialized with *maxsize* of zero. In such case, both :meth:`Queue.empty`
and :meth:`Queue.full` return ``True`` and :meth:`Queue.put` always blocks until
a call to :meth:`Queue.get` retrieves the item.

An interesting difference, made possible because of greenthreads, is
that :meth:`Queue.qsize`, :meth:`Queue.empty`, and :meth:`Queue.full` *can* be
used as indicators of whether the subsequent :meth:`Queue.get`
or :meth:`Queue.put` will not block.  The new methods :meth:`Queue.getting`
and :meth:`Queue.putting` report on the number of greenthreads blocking
in :meth:`put <Queue.put>` or :meth:`get <Queue.get>` respectively.
"""

import sys
import heapq
import collections
import traceback

from eventlet.event import Event
from eventlet.greenthread import getcurrent
from eventlet.hubs import get_hub
import queue as Stdlib_Queue
from eventlet.timeout import Timeout


__all__ = ['Queue', 'PriorityQueue', 'LifoQueue', 'LightQueue', 'Full', 'Empty']

_NONE = object()
Full = Stdlib_Queue.Full
Empty = Stdlib_Queue.Empty


class Waiter:
    """A low level synchronization class.

    Wrapper around greenlet's ``switch()`` and ``throw()`` calls that makes them safe:

    * switching will occur only if the waiting greenlet is executing :meth:`wait`
      method currently. Otherwise, :meth:`switch` and :meth:`throw` are no-ops.
    * any error raised in the greenlet is handled inside :meth:`switch` and :meth:`throw`

    The :meth:`switch` and :meth:`throw` methods must only be called from the :class:`Hub` greenlet.
    The :meth:`wait` method must be called from a greenlet other than :class:`Hub`.
    """
    __slots__ = ['greenlet']

    def __init__(self):
        self.greenlet = None

    def __repr__(self):
        if self.waiting:
            waiting = ' waiting'
        else:
            waiting = ''
        return '<%s at %s%s greenlet=%r>' % (
            type(self).__name__, hex(id(self)), waiting, self.greenlet,
        )

    def __str__(self):
        """
        >>> print(Waiter())
        <Waiter greenlet=None>
        """
        if self.waiting:
            waiting = ' waiting'
        else:
            waiting = ''
        return '<%s%s greenlet=%s>' % (type(self).__name__, waiting, self.greenlet)

    def __nonzero__(self):
        return self.greenlet is not None

    __bool__ = __nonzero__

    @property
    def waiting(self):
        return self.greenlet is not None

    def switch(self, value=None):
        """Wake up the greenlet that is calling wait() currently (if there is one).
        Can only be called from Hub's greenlet.
        """
        assert getcurrent() is get_hub(
        ).greenlet, "Can only use Waiter.switch method from the mainloop"
        if self.greenlet is not None:
            try:
                self.greenlet.switch(value)
            except Exception:
                traceback.print_exc()

    def throw(self, *throw_args):
        """Make greenlet calling wait() wake up (if there is a wait()).
        Can only be called from Hub's greenlet.
        """
        assert getcurrent() is get_hub(
        ).greenlet, "Can only use Waiter.switch method from the mainloop"
        if self.greenlet is not None:
            try:
                self.greenlet.throw(*throw_args)
            except Exception:
                traceback.print_exc()

    # XXX should be renamed to get() ? and the whole class is called Receiver?
    def wait(self):
        """Wait until switch() or throw() is called.
        """
        assert self.greenlet is None, 'This Waiter is already used by %r' % (self.greenlet, )
        self.greenlet = getcurrent()
        try:
            return get_hub().switch()
        finally:
            self.greenlet = None


class LightQueue:
    """
    This is a variant of Queue that behaves mostly like the standard
    :class:`Stdlib_Queue`.  It differs by not supporting the
    :meth:`task_done <Stdlib_Queue.task_done>` or
    :meth:`join <Stdlib_Queue.join>` methods, and is a little faster for
    not having that overhead.
    """

    def __init__(self, maxsize=None):
        if maxsize is None or maxsize < 0:  # None is not comparable in 3.x
            self.maxsize = None
        else:
            self.maxsize = maxsize
        self.getters = set()
        self.putters = set()
        self._event_unlock = None
        self._init(maxsize)

    # QQQ make maxsize into a property with setter that schedules unlock if necessary

    def _init(self, maxsize):
        self.queue = collections.deque()

    def _get(self):
        return self.queue.popleft()

    def _put(self, item):
        self.queue.append(item)

    def __repr__(self):
        return '<%s at %s %s>' % (type(self).__name__, hex(id(self)), self._format())

    def __str__(self):
        return '<%s %s>' % (type(self).__name__, self._format())

    def _format(self):
        result = 'maxsize=%r' % (self.maxsize, )
        if getattr(self, 'queue', None):
            result += ' queue=%r' % self.queue
        if self.getters:
            result += ' getters[%s]' % len(self.getters)
        if self.putters:
            result += ' putters[%s]' % len(self.putters)
        if self._event_unlock is not None:
            result += ' unlocking'
        return result

    def qsize(self):
        """Return the size of the queue."""
        return len(self.queue)

    def resize(self, size):
        """Resizes the queue's maximum size.

        If the size is increased, and there are putters waiting, they may be woken up."""
        # None is not comparable in 3.x
        if self.maxsize is not None and (size is None or size > self.maxsize):
            # Maybe wake some stuff up
            self._schedule_unlock()
        self.maxsize = size

    def putting(self):
        """Returns the number of greenthreads that are blocked waiting to put
        items into the queue."""
        return len(self.putters)

    def getting(self):
        """Returns the number of greenthreads that are blocked waiting on an
        empty queue."""
        return len(self.getters)

    def empty(self):
        """Return ``True`` if the queue is empty, ``False`` otherwise."""
        return not self.qsize()

    def full(self):
        """Return ``True`` if the queue is full, ``False`` otherwise.

        ``Queue(None)`` is never full.
        """
        # None is not comparable in 3.x
        return self.maxsize is not None and self.qsize() >= self.maxsize

    def put(self, item, block=True, timeout=None):
        """Put an item into the queue.

        If optional arg *block* is true and *timeout* is ``None`` (the default),
        block if necessary until a free slot is available. If *timeout* is
        a positive number, it blocks at most *timeout* seconds and raises
        the :class:`Full` exception if no free slot was available within that time.
        Otherwise (*block* is false), put an item on the queue if a free slot
        is immediately available, else raise the :class:`Full` exception (*timeout*
        is ignored in that case).
        """
        if self.maxsize is None or self.qsize() < self.maxsize:
            # there's a free slot, put an item right away
            self._put(item)
            if self.getters:
                self._schedule_unlock()
        elif not block and get_hub().greenlet is getcurrent():
            # we're in the mainloop, so we cannot wait; we can switch() to other greenlets though
            # find a getter and deliver an item to it
            while self.getters:
                getter = self.getters.pop()
                if getter:
                    self._put(item)
                    item = self._get()
                    getter.switch(item)
                    return
            raise Full
        elif block:
            waiter = ItemWaiter(item, block)
            self.putters.add(waiter)
            timeout = Timeout(timeout, Full)
            try:
                if self.getters:
                    self._schedule_unlock()
                result = waiter.wait()
                assert result is waiter, "Invalid switch into Queue.put: %r" % (result, )
                if waiter.item is not _NONE:
                    self._put(item)
            finally:
                timeout.cancel()
                self.putters.discard(waiter)
        elif self.getters:
            waiter = ItemWaiter(item, block)
            self.putters.add(waiter)
            self._schedule_unlock()
            result = waiter.wait()
            assert result is waiter, "Invalid switch into Queue.put: %r" % (result, )
            if waiter.item is not _NONE:
                raise Full
        else:
            raise Full

    def put_nowait(self, item):
        """Put an item into the queue without blocking.

        Only enqueue the item if a free slot is immediately available.
        Otherwise raise the :class:`Full` exception.
        """
        self.put(item, False)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args *block* is true and *timeout* is ``None`` (the default),
        block if necessary until an item is available. If *timeout* is a positive number,
        it blocks at most *timeout* seconds and raises the :class:`Empty` exception
        if no item was available within that time. Otherwise (*block* is false), return
        an item if one is immediately available, else raise the :class:`Empty` exception
        (*timeout* is ignored in that case).
        """
        if self.qsize():
            if self.putters:
                self._schedule_unlock()
            return self._get()
        elif not block and get_hub().greenlet is getcurrent():
            # special case to make get_nowait() runnable in the mainloop greenlet
            # there are no items in the queue; try to fix the situation by unlocking putters
            while self.putters:
                putter = self.putters.pop()
                if putter:
                    putter.switch(putter)
                    if self.qsize():
                        return self._get()
            raise Empty
        elif block:
            waiter = Waiter()
            timeout = Timeout(timeout, Empty)
            try:
                self.getters.add(waiter)
                if self.putters:
                    self._schedule_unlock()
                try:
                    return waiter.wait()
                except:
                    self._schedule_unlock()
                    raise
            finally:
                self.getters.discard(waiter)
                timeout.cancel()
        else:
            raise Empty

    def get_nowait(self):
        """Remove and return an item from the queue without blocking.

        Only get an item if one is immediately available. Otherwise
        raise the :class:`Empty` exception.
        """
        return self.get(False)

    def _unlock(self):
        try:
            while True:
                if self.qsize() and self.getters:
                    getter = self.getters.pop()
                    if getter:
                        try:
                            item = self._get()
                        except:
                            getter.throw(*sys.exc_info())
                        else:
                            getter.switch(item)
                elif self.putters and self.getters:
                    putter = self.putters.pop()
                    if putter:
                        getter = self.getters.pop()
                        if getter:
                            item = putter.item
                            # this makes greenlet calling put() not to call _put() again
                            putter.item = _NONE
                            self._put(item)
                            item = self._get()
                            getter.switch(item)
                            putter.switch(putter)
                        else:
                            self.putters.add(putter)
                elif self.putters and (self.getters or
                                       self.maxsize is None or
                                       self.qsize() < self.maxsize):
                    putter = self.putters.pop()
                    putter.switch(putter)
                elif self.putters and not self.getters:
                    full = [p for p in self.putters if not p.block]
                    if not full:
                        break
                    for putter in full:
                        self.putters.discard(putter)
                        get_hub().schedule_call_global(
                            0, putter.greenlet.throw, Full)
                else:
                    break
        finally:
            self._event_unlock = None  # QQQ maybe it's possible to obtain this info from libevent?
            # i.e. whether this event is pending _OR_ currently executing
        # testcase: 2 greenlets: while True: q.put(q.get()) - nothing else has a change to execute
        # to avoid this, schedule unlock with timer(0, ...) once in a while

    def _schedule_unlock(self):
        if self._event_unlock is None:
            self._event_unlock = get_hub().schedule_call_global(0, self._unlock)


class ItemWaiter(Waiter):
    __slots__ = ['item', 'block']

    def __init__(self, item, block):
        Waiter.__init__(self)
        self.item = item
        self.block = block


class Queue(LightQueue):
    '''Create a queue object with a given maximum size.

    If *maxsize* is less than zero or ``None``, the queue size is infinite.

    ``Queue(0)`` is a channel, that is, its :meth:`put` method always blocks
    until the item is delivered. (This is unlike the standard
    :class:`Stdlib_Queue`, where 0 means infinite size).

    In all other respects, this Queue class resembles the standard library,
    :class:`Stdlib_Queue`.
    '''

    def __init__(self, maxsize=None):
        LightQueue.__init__(self, maxsize)
        self.unfinished_tasks = 0
        self._cond = Event()

    def _format(self):
        result = LightQueue._format(self)
        if self.unfinished_tasks:
            result += ' tasks=%s _cond=%s' % (self.unfinished_tasks, self._cond)
        return result

    def _put(self, item):
        LightQueue._put(self, item)
        self._put_bookkeeping()

    def _put_bookkeeping(self):
        self.unfinished_tasks += 1
        if self._cond.ready():
            self._cond.reset()

    def task_done(self):
        '''Indicate that a formerly enqueued task is complete. Used by queue consumer threads.
        For each :meth:`get <Queue.get>` used to fetch a task, a subsequent call to
        :meth:`task_done` tells the queue that the processing on the task is complete.

        If a :meth:`join` is currently blocking, it will resume when all items have been processed
        (meaning that a :meth:`task_done` call was received for every item that had been
        :meth:`put <Queue.put>` into the queue).

        Raises a :exc:`ValueError` if called more times than there were items placed in the queue.
        '''

        if self.unfinished_tasks <= 0:
            raise ValueError('task_done() called too many times')
        self.unfinished_tasks -= 1
        if self.unfinished_tasks == 0:
            self._cond.send(None)

    def join(self):
        '''Block until all items in the queue have been gotten and processed.

        The count of unfinished tasks goes up whenever an item is added to the queue.
        The count goes down whenever a consumer thread calls :meth:`task_done` to indicate
        that the item was retrieved and all work on it is complete. When the count of
        unfinished tasks drops to zero, :meth:`join` unblocks.
        '''
        if self.unfinished_tasks > 0:
            self._cond.wait()


class PriorityQueue(Queue):
    '''A subclass of :class:`Queue` that retrieves entries in priority order (lowest first).

    Entries are typically tuples of the form: ``(priority number, data)``.
    '''

    def _init(self, maxsize):
        self.queue = []

    def _put(self, item, heappush=heapq.heappush):
        heappush(self.queue, item)
        self._put_bookkeeping()

    def _get(self, heappop=heapq.heappop):
        return heappop(self.queue)


class LifoQueue(Queue):
    '''A subclass of :class:`Queue` that retrieves most recently added entries first.'''

    def _init(self, maxsize):
        self.queue = []

    def _put(self, item):
        self.queue.append(item)
        self._put_bookkeeping()

    def _get(self):
        return self.queue.pop()
