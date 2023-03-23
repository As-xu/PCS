from pcs.base import pcs_bp
from flask_sqlalchemy import SQLAlchemy
import logging

logger = logging.getLogger(__name__)
db = SQLAlchemy()

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
        self.post_init()

    def register_blueprints(self):
        self.pcs_app.register_blueprint(pcs_bp)

    def config_sqlalchemy(self):
        db.init_app(self.pcs_app)
        self.pcs_app.db = db