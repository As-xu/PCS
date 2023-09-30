from .steady_db import connect

try:
    from _threading_local import local
except ImportError:
    from threading import local


class PersistentDBError(Exception):
    """常规持久数据库错误."""


class NotSupportedError(PersistentDBError):
    """持久数据库不支持 DB-API 模块."""


class PersistentDB:
    """用于持久 DB-API 2 连接的生成器。创建连接池后，可以使用 connection（） 来获取线程仿射、稳定的 DB-API 2 连接。
    """

    def __init__(
            self, creator,
            maxusage=None, setsession=None, failures=None, ping=1,
            closeable=False, threadlocal=None, *args, **kwargs):
        """
        threadlocal:用于表示线程本地数据的可选类, 将用于代替我们的 Python 实现（threading.local 更快，但不能在所有情况下都使用）
        closeable:如果设置为 true，则允许关闭连接，但默认情况下将静默忽略
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
        """获取稳定、非持久性的 DB-API 2 连接。"""
        return connect(
            self._creator, self._maxusage, self._setsession,
            self._failures, self._ping, self._closeable,
            *self._args, **self._kwargs)

    def connection(self):
        """获得稳定、持久的 DB-API 2 连接。
        可共享参数的存在只是为了与池数据库连接方法。 实际上，持久连接
        当然，绝不会与其他线程共享。
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

