from threading import Condition

from .steady_db import connect


class PooledDBError(Exception):
    """常规池数据库错误."""


class InvalidConnection(PooledDBError):
    """数据库连接无效."""


class NotSupportedError(PooledDBError):
    """PooledDB 不支持 DB模块."""


class TooManyConnections(PooledDBError):
    """打开的数据库连接过多."""


class PooledDB:
    """用于 DB连接的池。

    创建连接池后，可以使用 connection() 来获取池化、稳定的 DB连接。
    """

    def __init__(
            self, creator, mincached=0, maxcached=0,
            maxshared=0, maxconnections=0, blocking=False,
            maxusage=None, setsession=None, reset=True,
            failures=None, ping=1,
            *args, **kwargs):
        """ creator: 返回新 DB的任意函数连接对象或符合 DB的数据库模块
            mincached:池中空闲连接的初始数（0 表示启动时不建立连接）
            maxcached:池中空闲连接的最大数量（0 或无表示池大小不受限制）
            maxshared:最大共享连接数（0 或 None 表示所有连接都是专用的）当达到此最大数量时，连接数为共享（如果已请求共享）.
            maxconnections:通常允许的最大连接数（0 或 None 表示任意数量的连接）
            blocking:确定超过最大值时的行为（如果设置为 true，则阻止并等待，直到连接减少，否则将报告错误）
            maxusage:单个连接的最大重用次数（0 或无表示无限制重用）当达到此连接的最大使用数时，连接会自动重置（关闭并重新打开）.
            setsession:可用于准备的 SQL 命令的可选列表会话，例如 [“将日期样式设置为...”，“设置时区...”]
            reset:返回到池时应如何重置连接（如果为 False 或 None，则回滚以 begin（） 开头的事务，为了安全起见，总是发出回滚）
            failures:一个可选的异常类或一个异常类的元组，如果缺省值（操作错误、内部错误、接口）对于所使用的数据库模块来说是不够的，则应应用故障转移机制
            ping:确定何时应使用 ping（） 检查连接（
                0 = 无 = 从不，
                1 = 默认值 = 调用 _ping_check（） 时，
                2 = 每当创建游标时，
                4 = 执行查询时，
                7 = 总是，以及这些值的所有其他位组合）
            args，kwargs：应传递给创建者的参数,DB模块的函数或连接构造函数
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
        self._args, self._kwargs = args, kwargs
        self._blocking = blocking
        self._maxusage = maxusage
        self._setsession = setsession
        self._reset = reset
        self._failures = failures
        self._ping = ping
        if mincached is None:
            mincached = 0
        if maxcached is None:
            maxcached = 0
        if maxconnections is None:
            maxconnections = 0
        if maxcached:
            if maxcached < mincached:
                maxcached = mincached
            self._maxcached = maxcached
        else:
            self._maxcached = 0
        if threadsafety > 1 and maxshared:
            self._maxshared = maxshared
            self._shared_cache = []  # 共享连接的缓存
        else:
            self._maxshared = 0
        if maxconnections:
            if maxconnections < maxcached:
                maxconnections = maxcached
            if maxconnections < maxshared:
                maxconnections = maxshared
            self._maxconnections = maxconnections
        else:
            self._maxconnections = 0
        self._idle_cache = []  # 空闲连接的实际池
        self._lock = Condition()
        self._connections = 0
        # 建立初始数量的空闲数据库连接
        idle = [self.dedicated_connection() for i in range(mincached)]
        while idle:
            idle.pop().close()

    def steady_connection(self):
        """获取稳定的非池化DB连接."""
        return connect(
            self._creator, self._maxusage, self._setsession,
            self._failures, self._ping, True, *self._args, **self._kwargs)

    def connection(self, shareable=True):
        """从池中获取稳定的缓存 DB连接.如果设置了可共享并且底层 DB允许它，
        然后，可以与其他线程共享连接.
        """
        if shareable and self._maxshared:
            with self._lock:
                while (not self._shared_cache and self._maxconnections
                        and self._connections >= self._maxconnections):
                    self._wait_lock()
                if len(self._shared_cache) < self._maxshared:
                    # 共享缓存未满，获取专用连接
                    try:  # 首先尝试从空闲缓存中获取它
                        con = self._idle_cache.pop(0)
                    except IndexError:  # 否则获得新的连接
                        con = self.steady_connection()
                    else:
                        con._ping_check()  # 检查此连接
                    con = SharedDBConnection(con)
                    self._connections += 1
                else:  # 共享缓存已满或不允许更多连接
                    self._shared_cache.sort()  # 最少共享连接优先
                    con = self._shared_cache.pop(0)
                    while con.con._transaction:
                        # 不要共享事务中的连接
                        self._shared_cache.insert(0, con)
                        self._wait_lock()
                        self._shared_cache.sort()
                        con = self._shared_cache.pop(0)
                    con.con._ping_check()  # 检查底层连接
                    con.share()  # 将此链接共享
                # 将连接（放回）共享缓存中
                self._shared_cache.append(con)
                self._lock.notify()
            con = PooledSharedDBConnection(self, con)
        else:  # 尝试获取专用连接
            with self._lock:
                while (self._maxconnections
                        and self._connections >= self._maxconnections):
                    self._wait_lock()
                # 未达到连接限制，获取专用连接
                try:  # 首先尝试从空闲缓存中获取它
                    con = self._idle_cache.pop(0)
                except IndexError:  # 否则获得新的连接
                    con = self.steady_connection()
                else:
                    con._ping_check()  # 检查连接
                con = PooledDedicatedDBConnection(self, con)
                self._connections += 1
        return con

    def dedicated_connection(self):
        return self.connection(False)

    def unshare(self, con):
        """减少共享缓存中连接的份额."""
        with self._lock:
            con.unshare()
            shared = con.shared
            if not shared:  # 连接处于空闲状态
                try:  # 尝试删除它
                    self._shared_cache.remove(con)  # 从共享缓存
                except ValueError:
                    pass  # 连接池已经关闭
        if not shared:  # 连接已变为空闲状态
            self.cache(con.con)  # 因此将其添加到空闲缓存中

    def cache(self, con):
        """将专用连接放回空闲缓存中."""
        with self._lock:
            if not self._maxcached or len(self._idle_cache) < self._maxcached:
                con._reset(force=self._reset)  # 回滚可能的事务
                # 空闲缓存未满，所以把它放在那里
                self._idle_cache.append(con)  # 将其追加到空闲缓存
            else:  # 如果空闲缓存已满
                con.close()  # 然后关闭连接
            self._connections -= 1
            self._lock.notify()

    def close(self):
        """关闭池中的所有连接"""
        with self._lock:
            while self._idle_cache:  # 关闭所有空闲连接
                con = self._idle_cache.pop(0)
                try:
                    con.close()
                except Exception:
                    pass
            if self._maxshared:  # 关闭所有共享连接
                while self._shared_cache:
                    con = self._shared_cache.pop(0).con
                    try:
                        con.close()
                    except Exception:
                        pass
                    self._connections -= 1
            self._lock.notify_all()

    def __del__(self):
        """删除池"""
        try:
            self.close()
        except Exception:  # 内置异常可能不再存在
            pass

    def _wait_lock(self):
        """内置异常可能不再存在."""
        if not self._blocking:
            raise TooManyConnections
        self._lock.wait()


# 池连接的辅助类

class PooledDedicatedDBConnection:
    """池专用连接的辅助代理类."""

    def __init__(self, pool, con):
        """创建池专用连接.

        pool: 对应的池数据库实例
        con: 底层稳定数据库连接
        """
        # 基本初始化以使终结器工作
        self._con = None
        # 正确初始化连接
        if not con.threadsafety():
            raise NotSupportedError("Database module is not thread-safe.")
        self._pool = pool
        self._con = con

    def close(self):
        """关闭池专用连接."""
        # 不是实际关闭连接，而是将其返回到池以供将来重用.
        if self._con:
            self._pool.cache(self._con)
            self._con = None

    def __getattr__(self, name):
        """代理类的所有成员."""
        if self._con:
            return getattr(self._con, name)
        raise InvalidConnection

    def __del__(self):
        """删除共用连接."""
        try:
            self.close()
        except Exception:  # 内置异常可能不再存在
            pass

    def __enter__(self):
        """输入连接的运行时上下文."""
        return self

    def __exit__(self, *exc):
        """退出连接的运行时上下文."""
        self.close()


class SharedDBConnection:
    """共享连接的辅助类."""

    def __init__(self, con):
        """创建共享连接.

        con: 底层稳定数据库连接
        """
        self.con = con
        self.shared = 1

    def __lt__(self, other):
        if self.con._transaction == other.con._transaction:
            return self.shared < other.shared
        return not self.con._transaction

    def __le__(self, other):
        if self.con._transaction == other.con._transaction:
            return self.shared <= other.shared
        return not self.con._transaction

    def __eq__(self, other):
        return (self.con._transaction == other.con._transaction
                and self.shared == other.shared)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        return other.__lt__(self)

    def __ge__(self, other):
        return other.__le__(self)

    def share(self):
        """增加此连接的份额."""
        self.shared += 1

    def unshare(self):
        """减少此连接的份额."""
        self.shared -= 1


class PooledSharedDBConnection:
    """池共享连接的辅助代理类."""

    def __init__(self, pool, shared_con):
        """创建共用共享连接.

        pool: 对应的池数据库实例
        con: 底层的共享数据库
        """
        # 基本初始化以使终结器工作
        self._con = None
        # 正确初始化连接
        con = shared_con.con
        if not con.threadsafety() > 1:
            raise NotSupportedError("Database connection is not thread-safe.")
        self._pool = pool
        self._shared_con = shared_con
        self._con = con

    def close(self):
        """关闭共用共享连接."""
        # 不是实际关闭连接，只是取消共享它和/或将其返回到池中.
        if self._con:
            self._pool.unshare(self._shared_con)
            self._shared_con = self._con = None

    def __getattr__(self, name):
        """代理类的所有成员."""
        if self._con:
            return getattr(self._con, name)
        raise InvalidConnection

    def __del__(self):
        """删除池连接."""
        try:
            self.close()
        except Exception:  # 内置异常可能不再存在
            pass

    def __enter__(self):
        """进入连接的运行时上下文."""
        return self

    def __exit__(self, *exc):
        """退出连接的运行时上下文."""
        self.close()

    def set_conn(self, *args, **kwargs):
        self._con.set_conn(*args, **kwargs)