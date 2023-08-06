from flask import current_app
from pcs.common.base.base_table import BaseTable
from pcs.common.base.base_flask_app import BaseFlaskApp
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)
current_app: BaseFlaskApp


class BaseController:
    def __init__(self, request):
        self.request = request
        self.conn = current_app.get_db_connect()
        self.cur = self._get_cursor(self.conn)

    def _get_cursor(self, conn, name=None):
        return conn.cursor(name=name, cursor_factory=RealDictCursor)

    def get_table_obj(self, table_name):
        table_obj: BaseTable = current_app.get_table_obj(table_name, self.cur)
        return table_obj

    def get_table_objs(self, *table_names):
        table_objs = tuple(current_app.get_table_obj(name, self.conn) for name in table_names)
        return table_objs

    def get_table_obj_dict(self, table_names):
        table_obj_dict = {}
        for name in table_names:
            table_obj_dict[name] = current_app.get_table_obj(name, self.conn)
        return table_obj_dict

    def __del__(self):
        """Delete the steady connection."""
        try:
            self.cur.close()  # 确保连接已关闭
            self.conn.close()   # 确保连接已关闭
        except Exception:  # 内置异常可能不再存在
            pass

    def close_autocommit(self):
        self.conn.set_conn(autocommit=False)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()
