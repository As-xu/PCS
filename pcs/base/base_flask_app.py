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