import logging

logger = logging.getLogger(__name__)




class TableInfo:
    def __init__(self, table):
        self.__table = table


class Tables:
    def __init__(self):
        self.__tables = {}

    @property
    def tables(self):
        return self.__tables

    def add_table(self, table_class):
        if not issubclass(table_class, BaseTable):
            raise Exception("%s: 不是一个Table 类" % str(table_class))

        if self.exists_table(table_class.__name__):
            return None

        self.__tables[table_class.__name__] = table_class

    def exists_table(self, table_name):
        if table_name in self.__tables.keys():
            return True

        return False

    def get_table(self, table_name):
        if not self.exists_table(table_name):
            raise Exception("不存在此Table" % table_name)

        return self.__tables.get(table_name)


class BaseTable(object):
    __db_name = None
    __table_name = None

    @classmethod
    @property
    def table_name(cls):
        return cls.__table_name

    def search(self, domain, fields=None, offset=None, limit=None, order_by=None, is_distinct=None):
        return None

    def _query(self, sql, params=None):
        return None

    def paginate_query(self):
        return None

    def _paginate_query(self, sql, params=None):
        return None

    def delete(self):
        return None

    def batch_create(self):
        return None

    def update(self):
        return None

    def _write(self):
        return None

