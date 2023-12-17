from typing import Any


class Result:
    """
    通用的执行结果对象
    """
    def __init__(self, success: bool, msg: str = "", data: Any = None):
        self.success = success
        self.msg = msg
        self.data = data


