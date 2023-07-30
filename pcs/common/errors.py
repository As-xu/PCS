
class BaseError(Exception):
    """所有异常的基类"""


class InvalidScError(Exception):
    """非法的SQL条件"""