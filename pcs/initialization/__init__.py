from pcs.base import base_bp
from pcs.base.base_model import BaseModel
from pcs.extensions.db_link_extension.pooled_db import PooledDB
from flask_jwt_extended import JWTManager
from flask.logging import default_handler
import logging
import logging.handlers
import psycopg2
import os
import sys
import importlib
import json

logger = logging.getLogger(__name__)
jwt = JWTManager()


class Initializer:
    def __init__(self, app):
        super().__init__()
        self.pcs_app = app

    @property
    def flask_app(self):
        return self.pcs_app

    def pre_init(self):
        pass

    def post_init(self):
        pass

    def init_app(self):
        self.pre_init()
        self.init_log()
        self.register_blueprints()
        self.init_db()
        self.init_table()
        self.init_jwt()
        self.init_hook()
        self.post_init()

    def register_blueprints(self):
        self.pcs_app.register_blueprint(base_bp)

    def init_db(self):
        config = self.pcs_app.config
        db_conf_path = config.get("DB_CONF_PATH") or ""
        try:
            with open(db_conf_path, "r") as f:
                db_conf = json.load(f)
        except Exception as e:
            raise "读取数据库配置失败: %s" % str(e)

        if "main" not in db_conf.keys():
            raise "未配置main数据库"

        db_pool = self.pcs_app.db_pool
        for name, conf in db_conf.items():
            db_type = conf.pop("db_type", None)
            is_use = conf.pop("is_use", None)
            if not is_use:
                continue

            if db_type == "postgresql":
                creator = psycopg2
                db_pool[name] = PooledDB(
                    creator=creator,
                    **conf
                )
            # elif db_type == "mysql":
            #     creator = pymysql
            # elif db_type == "redis":
            #     creator = redis
            else:
                continue

    def init_table(self):
        pcs_module = sys.modules.get("pcs.model")

        tables = self.pcs_app.tables
        for key, module in pcs_module.__dict__.items():
            if not isinstance(module, type):
                continue

            if issubclass(module, BaseModel):
                tables.append(module)

            if module:
                pass

    def init_jwt(self):
        jwt.init_app(self.pcs_app)

    def init_log(self):
        from pcs.common.LoggingConfig import PCSFormatter

        log_file = self.pcs_app.config['LOG_FILE_NAME']
        log_dir = self.pcs_app.config['LOG_DIR']
        if 'LOG_LEVEL' in self.pcs_app.config.keys():
            log_level = self.pcs_app.config['LOG_LEVEL']
        else:
            log_level = logging.INFO
        if log_level not in [
            logging.NOTSET,
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ]:
            log_level = logging.INFO

        handler = logging.StreamHandler()
        format_str = '%(asctime)s %(process)s %(levelname)s %(name)s: %(message)s'

        logging.getLogger().removeHandler(default_handler)
        if os.environ.get("FLASK_ENV") == "development":
            try:
                log_file = os.path.join(log_dir, log_file)
                if log_dir and not os.path.isdir(log_dir):
                    os.makedirs(log_dir)
                if os.name == 'posix':
                    handler = logging.handlers.WatchedFileHandler(log_file)
                else:
                    handler = logging.FileHandler(log_file)
            except Exception:
                raise Exception("ERROR: 无法创建日志文件")

        handler.setFormatter(PCSFormatter(format_str))
        handler.setLevel(log_level)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

    def init_hook(self):
        from pcs.common.Hook import Hook
        # 在处理第一个请求前执行
        self.pcs_app.before_first_request(Hook.handle_before_first_request)
        # 在每次请求前执行
        self.pcs_app.before_request(Hook.handle_before_request)
        # 如果没有抛出错误，在每次请求后执行
        self.pcs_app.after_request(Hook.handle_after_request)
        # 在每次请求后执行, 捕获异常
        self.pcs_app.teardown_request(Hook.handle_teardown_request)

