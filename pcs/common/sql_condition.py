from pcs.common.common_const import QOP
from pcs.common.errors import InvalidQueryConditionError
import logging

logger = logging.getLogger(__name__)

__all__ = ['Sc']

class SqlCondition:
    def __init__(self, condition: list, raise_error=True):
        self.__condition = condition
        self.__valid = True
        self.__invalid_list = []
        self.check_valid(raise_error)

    @classmethod
    def parse2sc(cls, parse_condition):
        return cls(parse_condition, False)

    @property
    def condition(self):
        return self.__condition

    @property
    def valid(self):
        return self.__valid

    @property
    def invalid_msg(self):
        return "" if self.valid else "查询条件存在异常"

    @property
    def all_invalid_msg(self):
        msgs = []
        for invalid_item in self.__invalid_list:
            msgs.append("[{}]:{}".format(":".join(invalid_item[0]), invalid_item[1]))

        return "" if self.valid else "\n".join(msgs)

    def add_conditions(self, conditions):
        self.__condition.extend(conditions)
        self.check_valid()

    def check_valid(self, raise_error=True):
        self.__invalid_list = []
        self.__valid = True

        for condition in self.__condition:
            self.__check_condition(condition)

        if raise_error and not self.__valid:
            raise InvalidQueryConditionError(self.all_invalid_msg)

        return self.valid, self.invalid_msg

    def __check_condition(self, condition):
        if not isinstance(condition, (tuple, list)) and not condition:
            self.__valid = False
            self.__invalid_list.append(((str(condition),), '查询条件必须是元组或者列表'))
            return
        elif condition[0] == QOP.OR:
            for c in condition[1:]:
                self.__check_condition(c)
            return
        elif isinstance(condition[0], (tuple, list)):
            for c in condition:
                self.__check_condition(c)
            return

        if len(condition) == 2:
            operate = condition[0]
            field = condition[1]
            if operate not in (QOP.NULL, QOP.NOTNULL):
                self.__valid = False
                self.__invalid_list.append((condition, "二元查询条件的数据格式异常"))
            condition = (operate, field, "")
        elif len(condition) != 3:
            self.__valid = False
            self.__invalid_list.append((condition, "查询条件的数据格式异常"))

        operate = condition[0]
        field = condition[1]
        value = condition[2]
        if not QOP.have_op(operate):
            self.__valid = False
            self.__invalid_list.append((condition, "异常的查询操作符"))

        if not isinstance(value, (str, bool, int, float)):
            self.__valid = False
            self.__invalid_list.append((condition, "查询条件的值必须是字符串"))

        if not isinstance(field, str):
            self.__valid = False
            self.__invalid_list.append((condition, "查询条件的值必须是字符串"))

    def __str__(self):
        return ",".join(str(c) for c in self.__condition)

Sc = SqlCondition