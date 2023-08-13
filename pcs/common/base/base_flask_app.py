import logging
from flask import Flask
from .base_table import Tables
from .base_db import DBPool

logger = logging.getLogger(__name__)


class BaseFlaskApp(Flask):
    def __init__(self, *args, **kwargs):
        self.__tables = Tables()
        self.__db_pool = DBPool()
        self.dbs_conf = {}
        super(BaseFlaskApp, self).__init__(*args, **kwargs)

    @property
    def tables(self):
        return self.__tables

    @property
    def db_pool(self):
        return self.__db_pool

    def get_table_obj(self, table_name, conn, ):
        return self.__tables.get_table(table_name, conn)

    def add_table(self, table_class):
        self.__tables.add_table(table_class)

    def get_db_connect(self, db_name=None, autocommit=True):
        if not db_name:
            pool = self.__db_pool['main']
        else:
            if self.__db_pool.exists_pool(db_name):
                pool = self.__db_pool[db_name]
            else:
                return False

        conn = pool.connection()
        conn.set_conn(autocommit)
        return conn

    def dispatch_request(self):
        try:
            return super(BaseFlaskApp, self).dispatch_request()
        except Exception as e:
            raise