from pcs.common.sql_operator import *
from pcs.common.errors import InvalidScError
import logging

logger = logging.getLogger(__name__)


class Sc:
    def __init__(self, condition: list):
        self.__condition = condition
        self.valid = True
        self.invalid_msg = None
        self.check_valid()

    @classmethod
    def parse2sc(cls, parse_condition):
        condition = []
        return cls(condition)

    @property
    def condition(self):
        return self.__switch2complete()

    def add_condition(self, condition):
        self.__condition.append(condition)

    def add_conditions(self, conditions):
        self.__condition.extend(conditions)

    def __switch2complete(self):
        self.check_valid()

        complete_conditions = []
        for condition in self.__condition:
            if condition == SQL_OR:
                condition = (SQL_OR, SQL_OR, SQL_OR)

            if len(condition) == 2:
                condition = (condition[0], condition[1], "")

            complete_conditions.append({
                SQL_QUERY_FIELD: condition[0],
                SQL_QUERY_OPERATE: condition[1],
                SQL_QUERY_VALUE: condition[2],
            })

        return complete_conditions

    def check_valid(self, raise_error=True):
        for condition in self.__condition:
            if condition == SQL_OR:
                condition = (SQL_OR, SQL_OR, SQL_OR)

            if not isinstance(condition, tuple):
                self.valid = False
                self.invalid_msg = '查询条件{0}}必须是元组'.format(str(condition))

            if len(condition) == 2:
                field = condition[0]
                operate = condition[1]
                if operate not in [SQL_NULL, SQL_NOTNULL]:
                    self.valid = False
                    self.invalid_msg = "查询条件'{0}'至少三个数据".format(operate)
                condition = (field, operate, "")

            if len(condition) != 3:
                self.valid = False
                self.invalid_msg = '查询条件的形式是({0}, {1}, {2})'.format(SQL_QUERY_FIELD, SQL_QUERY_OPERATE, SQL_QUERY_VALUE)

            operate = condition[1]
            if operate not in SQL_QUERY_OPERATE_VALUES:
                self.valid = False
                self.invalid_msg = "不支持的操作符'{0}'".format(operate)

        if raise_error and not self.valid:
            raise InvalidScError(self.invalid_msg)

        return self.valid, self.invalid_msg