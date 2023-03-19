from flask_login import LoginManager
from pcs.base import pcs_bp
import logging

logger = logging.getLogger(__name__)


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
        # self.configure_login()
        self.register_blueprints()
        self.post_init()

    def register_blueprints(self):
        self.pcs_app.register_blueprint(pcs_bp)

    def configure_login(self):
        login_manager = LoginManager()
        login_manager.init_app(self.pcs_app)