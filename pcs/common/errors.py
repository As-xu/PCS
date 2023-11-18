
class BaseError(Exception):
    """所有异常的基类"""


class DBError(BaseError):
    """数据库异常"""
    code = 560
    description = (
        "数据库异常"
    )


class InvalidQueryConditionError(DBError):
    """非法的SQL条件"""
    code = 561
    description = (
        "非法的SQL条件"
    )


class DBExecuteError(DBError):
    """数据库执行异常"""
    code = 570
    description = (
        "执行SQL失败"
    )


class DBQueryError(DBExecuteError):
    """数据库查询异常"""
    code = 571
    description = (
        "数据库查询异常"
    )


class DBUpdateError(DBExecuteError):
    """数据库更新异常"""
    code = 572
    description = (
        "数据库更新异常"
    )


class DBCreateError(DBExecuteError):
    """数据库创建异常"""
    code = 573
    description = (
        "数据库创建异常"
    )


class DBDeleteError(DBExecuteError):
    """数据库删除异常"""
    code = 574
    description = (
        "DBDeleteError"
    )


