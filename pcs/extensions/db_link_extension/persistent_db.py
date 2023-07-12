from .steady_db import connect

try:
    # Prefer the pure Python version of threading.local.
    # The C implementation turned out to be problematic with mod_wsgi,
    # since it does not keep the thread-local data between requests.
    from _threading_local import local
except ImportError:
    # Fall back to the default version of threading.local.
    from threading import local


class PersistentDBError(Exception):
    """General PersistentDB error."""


class NotSupportedError(PersistentDBError):
    """DB-API module not supported by PersistentDB."""


class PersistentDB:
    """Generator for persistent DB-API 2 connections.

    After you have created the connection pool, you can use
    connection() to get thread-affine, steady DB-API 2 connections.
    """

    def __init__(
            self, creator,
            maxusage=None, setsession=None, failures=None, ping=1,
            closeable=False, threadlocal=None, *args, **kwargs):
        """Set up the persistent DB-API 2 connection generator.

        creator: either an arbitrary function returning new DB-API 2
            connection objects or a DB-API 2 compliant database module
        maxusage: maximum number of reuses of a single connection
            (number of database operations, 0 or None means unlimited)
            Whenever the limit is reached, the connection will be reset.
        setsession: optional list of SQL commands that may serve to prepare
            the session, e.g. ["set datestyle to ...", "set time zone ..."]
        failures: an optional exception class or a tuple of exception classes
            for which the connection failover mechanism shall be applied,
            if the default (OperationalError, InterfaceError, InternalError)
            is not adequate for the used database module
        ping: determines when the connection should be checked with ping()
            (0 = None = never, 1 = default = whenever it is requested,
            2 = when a cursor is created, 4 = when a query is executed,
            7 = always, and all other bit combinations of these values)
        closeable: if this is set to true, then closing connections will
            be allowed, but by default this will be silently ignored
        threadlocal: an optional class for representing thread-local data
            that will be used instead of our Python implementation
            (threading.local is faster, but cannot be used in all cases)
        args, kwargs: the parameters that shall be passed to the creator
            function or the connection constructor of the DB-API 2 module
        """
        try:
            threadsafety = creator.threadsafety
        except AttributeError:
            try:
                threadsafety = creator.dbapi.threadsafety
            except AttributeError:
                try:
                    if not callable(creator.connect):
                        raise AttributeError
                except AttributeError:
                    threadsafety = 1
                else:
                    threadsafety = 0
        if not threadsafety:
            raise NotSupportedError("Database module is not thread-safe.")
        self._creator = creator
        self._maxusage = maxusage
        self._setsession = setsession
        self._failures = failures
        self._ping = ping
        self._closeable = closeable
        self._args, self._kwargs = args, kwargs
        self.thread = (threadlocal or local)()

    def steady_connection(self):
        """Get a steady, non-persistent DB-API 2 connection."""
        return connect(
            self._creator, self._maxusage, self._setsession,
            self._failures, self._ping, self._closeable,
            *self._args, **self._kwargs)

    def connection(self, shareable=False):
        """Get a steady, persistent DB-API 2 connection.

        The shareable parameter exists only for compatibility with the
        PooledDB connection method.  In reality, persistent connections
        are of course never shared with other threads.
        """
        try:
            con = self.thread.connection
        except AttributeError:
            con = self.steady_connection()
            if not con.threadsafety():
                raise NotSupportedError("Database module is not thread-safe.")
            self.thread.connection = con
        con._ping_check()
        return con

    def dedicated_connection(self):
        """Alias for connection(shareable=False)."""
        return self.connection()
