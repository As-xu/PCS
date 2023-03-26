from pcs.base import pcs_bp
from pcs.common.Hook import *
from flask_sqlalchemy import SQLAlchemy
import logging

logger = logging.getLogger(__name__)
db = SQLAlchemy()


class Hook:
    @staticmethod
    def handle_before_first_request():
        logger.info("handle_before_first_request")

    @staticmethod
    def handle_before_request():
        logger.info("handle_before_request")

    @staticmethod
    def handle_after_request(response):
        logger.info("handle_after_request")
        return response

    @staticmethod
    def handle_teardown_request(e):
        logger.info("handle_teardown_request")


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
        self.register_blueprints()
        self.config_sqlalchemy()
        self.init_hook()
        self.post_init()

    def register_blueprints(self):
        self.pcs_app.register_blueprint(pcs_bp)

    def config_sqlalchemy(self):
        db.init_app(self.pcs_app)
        self.pcs_app.db = db

    def init_hook(self):
        # 在处理第一个请求前执行
        self.pcs_app.before_first_request(Hook.handle_before_first_request)
        # 在每次请求前执行
        self.pcs_app.before_request(Hook.handle_before_request)
        # 如果没有抛出错误，在每次请求后执行
        self.pcs_app.after_request(Hook.handle_after_request)
        # 在每次请求后执行, 捕获异常
        self.pcs_app.teardown_request(Hook.handle_teardown_request)

