from collections import deque
from contextlib import contextmanager
import sys
import time

from eventlet.pools import Pool
from eventlet import timeout
from eventlet import hubs
from eventlet.hubs.timer import Timer
from eventlet.greenthread import GreenThread


_MISSING = object()


class ConnectTimeout(Exception):
    pass


def cleanup_rollback(conn):
    conn.rollback()


class BaseConnectionPool(Pool):
    def __init__(self, db_module,
                 min_size=0, max_size=4,
                 max_idle=10, max_age=30,
                 connect_timeout=5,
                 cleanup=cleanup_rollback,
                 *args, **kwargs):
        """
        Constructs a pool with at least *min_size* connections and at most
        *max_size* connections.  Uses *db_module* to construct new connections.

        The *max_idle* parameter determines how long pooled connections can
        remain idle, in seconds.  After *max_idle* seconds have elapsed
        without the connection being used, the pool closes the connection.

        *max_age* is how long any particular connection is allowed to live.
        Connections that have been open for longer than *max_age* seconds are
        closed, regardless of idle time.  If *max_age* is 0, all connections are
        closed on return to the pool, reducing it to a concurrency limiter.

        *connect_timeout* is the duration in seconds that the pool will wait
        before timing out on connect() to the database.  If triggered, the
        timeout will raise a ConnectTimeout from get().

        The remainder of the arguments are used as parameters to the
        *db_module*'s connection constructor.
        """
        assert(db_module)
        self._db_module = db_module
        self._args = args
        self._kwargs = kwargs
        self.max_idle = max_idle
        self.max_age = max_age
        self.connect_timeout = connect_timeout
        self._expiration_timer = None
        self.cleanup = cleanup
        super().__init__(min_size=min_size, max_size=max_size, order_as_stack=True)

    def _schedule_expiration(self):
        """Sets up a timer that will call _expire_old_connections when the
        oldest connection currently in the free pool is ready to expire.  This
        is the earliest possible time that a connection could expire, thus, the
        timer will be running as infrequently as possible without missing a
        possible expiration.

        If this function is called when a timer is already scheduled, it does
        nothing.

        If max_age or max_idle is 0, _schedule_expiration likewise does nothing.
        """
        if self.max_age == 0 or self.max_idle == 0:
            # expiration is unnecessary because all connections will be expired
            # on put
            return

        if (self._expiration_timer is not None
                and not getattr(self._expiration_timer, 'called', False)):
            # the next timer is already scheduled
            return

        try:
            now = time.time()
            self._expire_old_connections(now)
            # the last item in the list, because of the stack ordering,
            # is going to be the most-idle
            idle_delay = (self.free_items[-1][0] - now) + self.max_idle
            oldest = min([t[1] for t in self.free_items])
            age_delay = (oldest - now) + self.max_age

            next_delay = min(idle_delay, age_delay)
        except (IndexError, ValueError):
            # no free items, unschedule ourselves
            self._expiration_timer = None
            return

        if next_delay > 0:
            # set up a continuous self-calling loop
            self._expiration_timer = Timer(next_delay, GreenThread(hubs.get_hub().greenlet).switch,
                                           self._schedule_expiration, [], {})
            self._expiration_timer.schedule()

    def _expire_old_connections(self, now):
        """Iterates through the open connections contained in the pool, closing
        ones that have remained idle for longer than max_idle seconds, or have
        been in existence for longer than max_age seconds.

        *now* is the current time, as returned by time.time().
        """
        original_count = len(self.free_items)
        expired = [
            conn
            for last_used, created_at, conn in self.free_items
            if self._is_expired(now, last_used, created_at)]

        new_free = [
            (last_used, created_at, conn)
            for last_used, created_at, conn in self.free_items
            if not self._is_expired(now, last_used, created_at)]
        self.free_items.clear()
        self.free_items.extend(new_free)

        # adjust the current size counter to account for expired
        # connections
        self.current_size -= original_count - len(self.free_items)

        for conn in expired:
            self._safe_close(conn, quiet=True)

    def _is_expired(self, now, last_used, created_at):
        """Returns true and closes the connection if it's expired.
        """
        if (self.max_idle <= 0 or self.max_age <= 0
                or now - last_used > self.max_idle
                or now - created_at > self.max_age):
            return True
        return False

    def _unwrap_connection(self, conn):
        """If the connection was wrapped by a subclass of
        BaseConnectionWrapper and is still functional (as determined
        by the __nonzero__, or __bool__ in python3, method), returns
        the unwrapped connection.  If anything goes wrong with this
        process, returns None.
        """
        base = None
        try:
            if conn:
                base = conn._base
                conn._destroy()
            else:
                base = None
        except AttributeError:
            pass
        return base

    def _safe_close(self, conn, quiet=False):
        """Closes the (already unwrapped) connection, squelching any
        exceptions.
        """
        try:
            conn.close()
        except AttributeError:
            pass  # conn is None, or junk
        except Exception:
            if not quiet:
                print("Connection.close raised: %s" % (sys.exc_info()[1]))

    def get(self):
        conn = super().get()

        # None is a flag value that means that put got called with
        # something it couldn't use
        if conn is None:
            try:
                conn = self.create()
            except Exception:
                # unconditionally increase the free pool because
                # even if there are waiters, doing a full put
                # would incur a greenlib switch and thus lose the
                # exception stack
                self.current_size -= 1
                raise

        # if the call to get() draws from the free pool, it will come
        # back as a tuple
        if isinstance(conn, tuple):
            _last_used, created_at, conn = conn
        else:
            created_at = time.time()

        # wrap the connection so the consumer can call close() safely
        wrapped = PooledConnectionWrapper(conn, self)
        # annotating the wrapper so that when it gets put in the pool
        # again, we'll know how old it is
        wrapped._db_pool_created_at = created_at
        return wrapped

    def put(self, conn, cleanup=_MISSING):
        created_at = getattr(conn, '_db_pool_created_at', 0)
        now = time.time()
        conn = self._unwrap_connection(conn)

        if self._is_expired(now, now, created_at):
            self._safe_close(conn, quiet=False)
            conn = None
        elif cleanup is not None:
            if cleanup is _MISSING:
                cleanup = self.cleanup
            # by default, call rollback in case the connection is in the middle
            # of a transaction. However, rollback has performance implications
            # so optionally do nothing or call something else like ping
            try:
                if conn:
                    cleanup(conn)
            except Exception as e:
                # we don't care what the exception was, we just know the
                # connection is dead
                print("WARNING: cleanup %s raised: %s" % (cleanup, e))
                conn = None
            except:
                conn = None
                raise

        if conn is not None:
            super().put((now, created_at, conn))
        else:
            # wake up any waiters with a flag value that indicates
            # they need to manufacture a connection
            if self.waiting() > 0:
                super().put(None)
            else:
                # no waiters -- just change the size
                self.current_size -= 1
        self._schedule_expiration()

    @contextmanager
    def item(self, cleanup=_MISSING):
        conn = self.get()
        try:
            yield conn
        finally:
            self.put(conn, cleanup=cleanup)

    def clear(self):
        """Close all connections that this pool still holds a reference to,
        and removes all references to them.
        """
        if self._expiration_timer:
            self._expiration_timer.cancel()
        free_items, self.free_items = self.free_items, deque()
        for item in free_items:
            # Free items created using min_size>0 are not tuples.
            conn = item[2] if isinstance(item, tuple) else item
            self._safe_close(conn, quiet=True)
            self.current_size -= 1

    def __del__(self):
        self.clear()


class TpooledConnectionPool(BaseConnectionPool):
    """A pool which gives out :class:`~eventlet.tpool.Proxy`-based database
    connections.
    """

    def create(self):
        now = time.time()
        return now, now, self.connect(
            self._db_module, self.connect_timeout, *self._args, **self._kwargs)

    @classmethod
    def connect(cls, db_module, connect_timeout, *args, **kw):
        t = timeout.Timeout(connect_timeout, ConnectTimeout())
        try:
            from eventlet import tpool
            conn = tpool.execute(db_module.connect, *args, **kw)
            return tpool.Proxy(conn, autowrap_names=('cursor',))
        finally:
            t.cancel()


class RawConnectionPool(BaseConnectionPool):
    """A pool which gives out plain database connections.
    """

    def create(self):
        now = time.time()
        return now, now, self.connect(
            self._db_module, self.connect_timeout, *self._args, **self._kwargs)

    @classmethod
    def connect(cls, db_module, connect_timeout, *args, **kw):
        t = timeout.Timeout(connect_timeout, ConnectTimeout())
        try:
            return db_module.connect(*args, **kw)
        finally:
            t.cancel()


# default connection pool is the tpool one
ConnectionPool = TpooledConnectionPool


class GenericConnectionWrapper:
    def __init__(self, baseconn):
        self._base = baseconn

    # Proxy all method calls to self._base
    # FIXME: remove repetition; options to consider:
    # * for name in (...):
    #     setattr(class, name, lambda self, *a, **kw: getattr(self._base, name)(*a, **kw))
    # * def __getattr__(self, name): if name in (...): return getattr(self._base, name)
    # * other?
    def __enter__(self):
        return self._base.__enter__()

    def __exit__(self, exc, value, tb):
        return self._base.__exit__(exc, value, tb)

    def __repr__(self):
        return self._base.__repr__()

    _proxy_funcs = (
        'affected_rows',
        'autocommit',
        'begin',
        'change_user',
        'character_set_name',
        'close',
        'commit',
        'cursor',
        'dump_debug_info',
        'errno',
        'error',
        'errorhandler',
        'get_server_info',
        'insert_id',
        'literal',
        'ping',
        'query',
        'rollback',
        'select_db',
        'server_capabilities',
        'set_character_set',
        'set_isolation_level',
        'set_server_option',
        'set_sql_mode',
        'show_warnings',
        'shutdown',
        'sqlstate',
        'stat',
        'store_result',
        'string_literal',
        'thread_id',
        'use_result',
        'warning_count',
    )


for _proxy_fun in GenericConnectionWrapper._proxy_funcs:
    # excess wrapper for early binding (closure by value)
    def _wrapper(_proxy_fun=_proxy_fun):
        def _proxy_method(self, *args, **kwargs):
            return getattr(self._base, _proxy_fun)(*args, **kwargs)
        _proxy_method.func_name = _proxy_fun
        _proxy_method.__name__ = _proxy_fun
        _proxy_method.__qualname__ = 'GenericConnectionWrapper.' + _proxy_fun
        return _proxy_method
    setattr(GenericConnectionWrapper, _proxy_fun, _wrapper(_proxy_fun))
del GenericConnectionWrapper._proxy_funcs
del _proxy_fun
del _wrapper


class PooledConnectionWrapper(GenericConnectionWrapper):
    """A connection wrapper where:
    - the close method returns the connection to the pool instead of closing it directly
    - ``bool(conn)`` returns a reasonable value
    - returns itself to the pool if it gets garbage collected
    """

    def __init__(self, baseconn, pool):
        super().__init__(baseconn)
        self._pool = pool

    def __nonzero__(self):
        return (hasattr(self, '_base') and bool(self._base))

    __bool__ = __nonzero__

    def _destroy(self):
        self._pool = None
        try:
            del self._base
        except AttributeError:
            pass

    def close(self):
        """Return the connection to the pool, and remove the
        reference to it so that you can't use it again through this
        wrapper object.
        """
        if self and self._pool:
            self._pool.put(self)
        self._destroy()

    def __del__(self):
        return  # this causes some issues if __del__ is called in the
        # main coroutine, so for now this is disabled
        # self.close()


class DatabaseConnector:
    """
    This is an object which will maintain a collection of database
    connection pools on a per-host basis.
    """

    def __init__(self, module, credentials,
                 conn_pool=None, *args, **kwargs):
        """constructor
        *module*
            Database module to use.
        *credentials*
            Mapping of hostname to connect arguments (e.g. username and password)
        """
        assert(module)
        self._conn_pool_class = conn_pool
        if self._conn_pool_class is None:
            self._conn_pool_class = ConnectionPool
        self._module = module
        self._args = args
        self._kwargs = kwargs
        # this is a map of hostname to username/password
        self._credentials = credentials
        self._databases = {}

    def credentials_for(self, host):
        if host in self._credentials:
            return self._credentials[host]
        else:
            return self._credentials.get('default', None)

    def get(self, host, dbname):
        """Returns a ConnectionPool to the target host and schema.
        """
        key = (host, dbname)
        if key not in self._databases:
            new_kwargs = self._kwargs.copy()
            new_kwargs['db'] = dbname
            new_kwargs['host'] = host
            new_kwargs.update(self.credentials_for(host))
            dbpool = self._conn_pool_class(
                self._module, *self._args, **new_kwargs)
            self._databases[key] = dbpool

        return self._databases[key]
