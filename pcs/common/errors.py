
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


class GenerateSQLError(BaseError):
    """生成SQL异常"""
    code = 562
    description = (
        "生成SQL异常"
    )

class DBExecuteError(DBError):
    """数据库执行异常"""
    code = 570
    description = (
        "执行SQL失败"
    )


class DBQueryError(DBExecuteError):
    """查询数据异常"""
    code = 571
    description = (
        "查询数据异常"
    )


class DBUpdateError(DBExecuteError):
    """更新数据异常"""
    code = 572
    description = (
        "更新数据异常"
    )


class DBCreateError(DBExecuteError):
    """创建数据异常"""
    code = 573
    description = (
        "创建数据异常"
    )


class DBDeleteError(DBExecuteError):
    """删除数据异常"""
    code = 574
    description = (
        "删除数据异常"
    )


