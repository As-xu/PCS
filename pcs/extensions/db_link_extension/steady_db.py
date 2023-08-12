import sys


class SteadyDBError(Exception):
    """通用Steady数据库错误。"""


class InvalidCursor(SteadyDBError):
    """数据库游标无效"""


def connect(
        creator, maxusage=None, setsession=None,
        failures=None, ping=1, closeable=True, *args, **kwargs):
    """closeable: 如果设置为 false，则关闭连接将被静默忽略，但默认情况下可以关闭连接
    """
    return SteadyDBConnection(
        creator, maxusage, setsession,
        failures, ping, closeable, *args, **kwargs)


class SteadyDBConnection:
    """一个强健版本的DB链接"""

    def __init__(
            self, creator, maxusage=None, setsession=None,
            failures=None, ping=1, closeable=True, *args, **kwargs):
        """创建一个强健的DB链接."""
        # 基本初始化以使终结器工作
        self._con = None
        self._closed = True
        # 正确初始化连接
        try:
            self._creator = creator.connect
            try:
                if creator.dbapi.connect:
                    self._dbapi = creator.dbapi
            except AttributeError:
                self._dbapi = creator
        except AttributeError:
            # 尝试通过连接创建器查找 DB 模块
            self._creator = creator
            try:
                self._dbapi = creator.dbapi
            except AttributeError:
                try:
                    self._dbapi = sys.modules[creator.__module__]
                    if self._dbapi.connect != creator:
                        raise AttributeError
                except (AttributeError, KeyError):
                    self._dbapi = None
        try:
            self._threadsafety = creator.threadsafety
        except AttributeError:
            try:
                self._threadsafety = self._dbapi.threadsafety
            except AttributeError:
                self._threadsafety = None
        if not callable(self._creator):
            raise TypeError(f"{creator!r} is not a connection provider.")
        if maxusage is None:
            maxusage = 0
        if not isinstance(maxusage, int):
            raise TypeError("'maxusage' must be an integer value.")
        self._maxusage = maxusage
        self._setsession_sql = setsession
        if failures is not None and not isinstance(
                failures, tuple) and not issubclass(failures, Exception):
            raise TypeError("'failures' must be a tuple of exceptions.")
        self._failures = failures
        self._ping = ping if isinstance(ping, int) else 0
        self._closeable = closeable
        self._args, self._kwargs = args, kwargs
        self._store(self._create())

    def __enter__(self):
        """输入连接对象的运行时上下文."""
        return self

    def __exit__(self, *exc):
        """退出连接对象的运行时上下文.

        这不会关闭连接，但会结束事务.
        """
        if exc[0] is None and exc[1] is None and exc[2] is None:
            self.commit()
        else:
            self.rollback()

    def _create(self):
        """使用创建器函数创建新连接."""
        con = self._creator(*self._args, **self._kwargs)
        try:
            try:
                if self._dbapi.connect != self._creator:
                    raise AttributeError
            except AttributeError:
                # 尝试通过连接本身查找 DB 模块
                try:
                    mod = con.__module__
                except AttributeError:
                    mod = None
                while mod:
                    try:
                        self._dbapi = sys.modules[mod]
                        if not callable(self._dbapi.connect):
                            raise AttributeError
                    except (AttributeError, KeyError):
                        pass
                    else:
                        break
                    i = mod.rfind('.')
                    if i < 0:
                        mod = None
                    else:
                        mod = mod[:i]
                else:
                    try:
                        mod = con.OperationalError.__module__
                    except AttributeError:
                        mod = None
                    while mod:
                        try:
                            self._dbapi = sys.modules[mod]
                            if not callable(self._dbapi.connect):
                                raise AttributeError
                        except (AttributeError, KeyError):
                            pass
                        else:
                            break
                        i = mod.rfind('.')
                        if i < 0:
                            mod = None
                        else:
                            mod = mod[:i]
                    else:
                        self._dbapi = None
            if self._threadsafety is None:
                try:
                    self._threadsafety = self._dbapi.threadsafety
                except AttributeError:
                    try:
                        self._threadsafety = con.threadsafety
                    except AttributeError:
                        pass
            if self._failures is None:
                try:
                    self._failures = (
                        self._dbapi.OperationalError,
                        self._dbapi.InterfaceError,
                        self._dbapi.InternalError)
                except AttributeError:
                    try:
                        self._failures = (
                            self._creator.OperationalError,
                            self._creator.InterfaceError,
                            self._creator.InternalError)
                    except AttributeError:
                        try:
                            self._failures = (
                                con.OperationalError,
                                con.InterfaceError,
                                con.InternalError)
                        except AttributeError:
                            raise AttributeError(
                                "Could not determine failure exceptions (please set failures or creator.dbapi).")
            if isinstance(self._failures, tuple):
                self._failure = self._failures[0]
            else:
                self._failure = self._failures
            self._setsession(con)
        except Exception as error:
            # 无法确定数据库模块或无法准备会话
            try:  # 首先关闭连接
                con.close()
            except Exception:
                pass
            raise error  # 再次引发原始错误
        return con

    def _setsession(self, con=None):
        """执行 SQL 命令以进行会话准备."""
        if con is None:
            con = self._con
        if self._setsession_sql:
            cursor = con.cursor()
            for sql in self._setsession_sql:
                cursor.execute(sql)
            cursor.close()

    def set_conn(self, autocommit=False, *args, **kwargs):
        self._con.autocommit = autocommit
        return None

    def _store(self, con):
        """存储数据库连接以供后续使用."""
        self._con = con
        self._transaction = False
        self._closed = False
        self._usage = 0

    def _close(self):
        """关闭链接.
        您始终可以使用此方法关闭艰难的连接 如果您多次关闭它，它不会引起异常.
        """
        if not self._closed:
            try:
                self._con.close()
            except Exception:
                pass
            self._transaction = False
            self._closed = True

    def _reset(self, force=False):
        """重置连接。

        如果强制或连接在事务中，则回滚。
        """
        if not self._closed and (force or self._transaction):
            try:
                self.rollback()
            except Exception:
                pass

    def _ping_check(self, ping=1, reconnect=True):
        """使用 ping（） 检查连接是否仍处于活动状态。
           如果基础连接未处于活动状态，并且相应地设置了 ping 参数，
           则将重新创建连接，除非连接当前位于事务内。
        """
        if ping & self._ping:
            try:  # 如果可能，请 ping 连接
                try:  # pass a reconnect=False flag if this is supported
                    alive = self._con.ping(False)
                except TypeError:  # 传递重新连接=False 标志（如果支持）
                    alive = self._con.ping()
            except (AttributeError, IndexError, TypeError, ValueError):
                self._ping = 0  # ping（） 不可用
                alive = None
                reconnect = False
            except Exception:
                alive = False
            else:
                if alive is None:
                    alive = True
                if alive:
                    reconnect = False
            if reconnect and not self._transaction:
                try:  # 尝试重新打开连接
                    con = self._create()
                except Exception:
                    pass
                else:
                    self._close()
                    self._store(con)
                    alive = True
            return alive

    def dbapi(self):
        """返回连接的基础 DB-API 2 模块."""
        if self._dbapi is None:
            raise AttributeError("Could not determine DB-API 2 module (please set creator.dbapi).")
        return self._dbapi

    def threadsafety(self):
        """返回连接的线程安全级别."""
        if self._threadsafety is None:
            if self._dbapi is None:
                raise AttributeError(
                    "Could not determine threadsafety (please set creator.dbapi or creator.threadsafety).")
            return 0
        return self._threadsafety

    def close(self):
        """关闭连接.

        默认情况下，您可以关闭的连接，如果您多次关闭它，它不会引发异常。

        您可以通过将可关闭参数设置为 false 来禁止关闭连接。 在这种情况下，关闭强连接将被静默忽略。
        """
        if self._closeable:
            self._close()
        elif self._transaction:
            self._reset()

    def begin(self, *args, **kwargs):
        """指示事务的开始.

        在事务期间，连接不会被透明地替换，并且所有错误都将引发到应用程序.

        如果底层驱动程序支持此方法，则将使用给定的参数调用它（例如，对于分布式事务）
        """
        self._transaction = True
        try:
            begin = self._con.begin
        except AttributeError:
            pass
        else:
            begin(*args, **kwargs)

    def commit(self):
        """提交任何待处理事务."""
        self._transaction = False
        try:
            self._con.commit()
        except self._failures as error:  # 如果无法提交
            try:  # 尝试重新打开连接
                con = self._create()
            except Exception:
                pass
            else:
                self._close()
                self._store(con)
            raise error  # 重新引发原始错误

    def rollback(self):
        """Rollback pending transaction."""
        self._transaction = False
        try:
            self._con.rollback()
        except self._failures as error:  # 无法回滚
            try:  # 尝试重新打开连接
                con = self._create()
            except Exception:
                pass
            else:
                self._close()
                self._store(con)
            raise error  # 重新引发原始错误

    def cancel(self):
        """取消长时间运行的事务.

        如果基础驱动程序支持此方法，则将调用.
        """
        self._transaction = False
        try:
            cancel = self._con.cancel
        except AttributeError:
            pass
        else:
            cancel()

    def ping(self, *args, **kwargs):
        """Ping 链接."""
        return self._con.ping(*args, **kwargs)

    def _cursor(self, *args, **kwargs):
        """一个强硬的cursor()方法. """
        #  args and kwargs 不是标准的一部分, 但是一些数据库模块似乎使用这些。
        transaction = self._transaction
        if not transaction:
            self._ping_check(2)
        try:
            # 检查连接是否使用得太频繁
            if (self._maxusage and self._usage >= self._maxusage
                    and not transaction):
                raise self._failure
            cursor = self._con.cursor(*args, **kwargs)  # 尝试获取游标
        except self._failures as error:  # 获取游标时出错
            try:  # 尝试重新打开连接
                con = self._create()
            except Exception:
                pass
            else:
                try:  # 并再尝试一次以获取光标
                    cursor = con.cursor(*args, **kwargs)
                except Exception:
                    pass
                else:
                    self._close()
                    self._store(con)
                    if transaction:
                        raise error  # 再次引发原始错误
                    return cursor
                try:
                    con.close()
                except Exception:
                    pass
            if transaction:
                self._transaction = False
            raise error  # 再次引发原始错误
        return cursor

    def cursor(self, *args, **kwargs):
        """使用连接返回新的游标对象."""
        return SteadyDBCursor(self, *args, **kwargs)

    def __del__(self):
        """Delete the steady connection."""
        try:
            self._close()  # 确保连接已关闭
        except:  # 内置异常可能不再存在
            pass


class SteadyDBCursor:
    """A "tough" version of DB-API 2 cursors."""

    def __init__(self, con, *args, **kwargs):
        """Create a "tough" DB-API 2 cursor."""
        # 基本初始化以使终结器工作
        self._cursor = None
        self._closed = True
        # 正确初始化游标
        self._con = con
        self._args, self._kwargs = args, kwargs
        self._clearsizes()
        try:
            self._cursor = con._cursor(*args, **kwargs)
        except AttributeError:
            raise TypeError(f"{con!r} is not a SteadyDBConnection.")
        self._closed = False

    def __enter__(self):
        """输入游标对象的运行时上下文."""
        return self

    def __exit__(self, *exc):
        """退出游标对象的运行时上下文."""
        self.close()

    def __iter__(self):
        """使游标与迭代协议兼容."""
        cursor = self._cursor
        try:  # 使用原始游标提供的迭代器
            return iter(cursor)
        except TypeError:  # 创建迭代器（如果未提供）
            return iter(cursor.fetchone, None)

    def setinputsizes(self, sizes):
        """存储输入大小，以防需要重新打开光标."""
        self._inputsizes = sizes

    def setoutputsize(self, size, column=None):
        """存储输出大小，以防需要重新打开光标."""
        self._outputsizes[column] = size

    def _clearsizes(self):
        """清除存储的输入和输出大小."""
        self._inputsizes = []
        self._outputsizes = {}

    def _setsizes(self, cursor=None):
        """设置存储的输入和输出大小以执行游标."""
        if cursor is None:
            cursor = self._cursor
        if self._inputsizes:
            cursor.setinputsizes(self._inputsizes)
        for column, size in self._outputsizes.items():
            if column is None:
                cursor.setoutputsize(size)
            else:
                cursor.setoutputsize(size, column)

    def close(self):
        """关闭强硬光标.
        如果您多次关闭它，它不会引起异常
        """
        if not self._closed:
            try:
                self._cursor.close()
            except Exception:
                pass
            self._closed = True

    def _get_tough_method(self, name):
        """返回给定游标方法的“强硬”版本."""
        def tough_method(*args, **kwargs):
            execute = name.startswith('execute')
            con = self._con
            transaction = con._transaction
            if not transaction:
                con._ping_check(4)
            try:
                # 检查连接是否使用得太频繁
                if (con._maxusage and con._usage >= con._maxusage
                        and not transaction):
                    raise con._failure
                if execute:
                    self._setsizes()
                method = getattr(self._cursor, name)
                result = method(*args, **kwargs)  # 尝试执行
                if execute:
                    self._clearsizes()
            except con._failures as error:  # 执行错误
                if not transaction:
                    try:
                        cursor2 = con._cursor(
                            *self._args, **self._kwargs)  # 打开新游标
                    except Exception:
                        pass
                    else:
                        try:  # 并再次尝试执行
                            if execute:
                                self._setsizes(cursor2)
                            method = getattr(cursor2, name)
                            result = method(*args, **kwargs)
                            if execute:
                                self._clearsizes()
                        except Exception:
                            pass
                        else:
                            self.close()
                            self._cursor = cursor2
                            con._usage += 1
                            return result
                        try:
                            cursor2.close()
                        except Exception:
                            pass
                try:  # 尝试重新打开连接
                    con2 = con._create()
                except Exception:
                    pass
                else:
                    try:
                        cursor2 = con2.cursor(
                            *self._args, **self._kwargs)  # 打开新游标
                    except Exception:
                        pass
                    else:
                        if transaction:
                            self.close()
                            con._close()
                            con._store(con2)
                            self._cursor = cursor2
                            raise error  # 再次引发原始错误
                        error2 = None
                        try:  # 再试一次执行
                            if execute:
                                self._setsizes(cursor2)
                            method2 = getattr(cursor2, name)
                            result = method2(*args, **kwargs)
                            if execute:
                                self._clearsizes()
                        except error.__class__:  # 相同的执行错误
                            use2 = False
                            error2 = error
                        except Exception as error:  # 其他执行错误
                            use2 = True
                            error2 = error
                        else:
                            use2 = True
                        if use2:
                            self.close()
                            con._close()
                            con._store(con2)
                            self._cursor = cursor2
                            con._usage += 1
                            if error2:
                                raise error2  # 引发另一个错误
                            return result
                        try:
                            cursor2.close()
                        except Exception:
                            pass
                    try:
                        con2.close()
                    except Exception:
                        pass
                if transaction:
                    self._transaction = False
                raise error  # 再次引发原始错误
            else:
                con._usage += 1
                return result
        return tough_method

    def __getattr__(self, name):
        """继承基础游标的方法和属性."""
        if self._cursor:
            if name.startswith(('execute', 'call')):
                # 制作一个强硬的执行方法
                return self._get_tough_method(name)
            return getattr(self._cursor, name)
        raise InvalidCursor

    def __del__(self):
        """Delete the steady cursor."""
        try:
            self.close()  # 确保光标已关闭
        except:  # 内置异常可能不再存在
            pass
