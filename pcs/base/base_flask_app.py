from flask import Flask
from .base_table import Tables
from .base_db import DBPool
import logging

logger = logging.getLogger(__name__)


class BaseFlaskApp(Flask):

    def __init__(self, *args, **kwargs):
        self.__tables = Tables()
        self.__db_pool = DBPool()
        super(BaseFlaskApp, self).__init__(*args, **kwargs)

    @property
    def tables(self):
        return self.__tables

    @property
    def db_pool(self):
        return self.__db_pool

    def get_table_obj(self, table_name):
        table_class = self.__tables.get_table(table_name)
        return table_class()

    def gto(self, table_name):
        return self.get_table_obj(table_name)

    def add_table(self, table_class):
        self.__tables.add_table(table_class)
