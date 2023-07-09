from pcs.base import base_bp
from pcs.base.base_model import BaseModel, BaseQuery
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask.logging import default_handler
import os
import logging
import logging.handlers


logger = logging.getLogger(__name__)
db = SQLAlchemy(model_class=BaseModel, query_class=BaseQuery)
jwt = JWTManager()


class Initializer:
    def __init__(self, app):
        super().__init__()

        self.pcs_app = app
        self.config = app.config
        self.manifest = {}

    @property
    def flask_app(self):
        return self.pcs_app

    def pre_init(self):
        pass

    def post_init(self):
        pass

    def init_app(self):
        self.pre_init()
        self.setup_log()
        self.register_blueprints()
        self.config_sqlalchemy()
        self.config_jwt()
        self.init_hook()
        self.post_init()

    def register_blueprints(self):
        self.pcs_app.register_blueprint(base_bp)

    def config_sqlalchemy(self):
        db.init_app(self.pcs_app)
        self.pcs_app.db = db
        db.Model.db_engine = db.engine

    def config_jwt(self):
        jwt.init_app(self.pcs_app)

    def setup_log(self):
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

