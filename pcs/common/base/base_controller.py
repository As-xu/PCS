import logging
from flask import current_app
from flask_jwt_extended import get_jwt_identity
from psycopg2.extras import RealDictCursor
from pcs.common.result import Result
from pcs.common.base.base_table import BaseTable
from pcs.common.base.base_flask_app import BaseFlaskApp


logger = logging.getLogger(__name__)
current_app: BaseFlaskApp


class BaseController:
    def __init__(self, request):
        self.request_ip = request.remote_addr
        self.request_path = request.path
        jwt_identity = get_jwt_identity() or {}
        self.have_identity = True if jwt_identity else False
        self.user_id = jwt_identity.get("user_id")
        self.user_name = jwt_identity.get("user_name")
        self.conn = current_app.get_db_connect()
        self.cur = self._get_cursor(self.conn)
        self.tables = current_app.tables

    def _get_cursor(self, conn, name=None):
        return conn.cursor(name=name, cursor_factory=RealDictCursor)

    def get_table_obj(self, table_name):
        table_obj: BaseTable = self.tables.__getattribute__(table_name)(self)
        return table_obj

    def get_table(self, table_class: type):
        table : BaseTable = table_class(self)
        return table

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

    def return_res(self, success, msg="", data=None):
        return Result(success, msg=msg, data=data)

    def return_ok(self, msg="", data=None, log=False):
        return self.return_res(True, msg=msg, data=data)

    def return_failure(self, msg="", data=None, log=False):
        if log:
            f = logging.currentframe()
            lno, func = "(unknown file)", "(unknown function)"
            if f is not None:
                lno, func =  f.f_lineno, f.f_code.co_name
            message = "%s \n%s line:%s MSG:%s \n%s" % ("*" * 20, func, lno, msg, "*" * 20)
            logger.info(message)

        return self.return_res(False, msg=msg, data=data)

    def return_data(self, data=None):
        return self.return_res(False, msg="", data=data)