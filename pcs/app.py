import logging

logger = logging.getLogger('pcs')

from pcs.initialization import Initializer
from pcs.base.base_flask_app import BaseFlaskApp


def create_app(config=None):
    app = BaseFlaskApp(__name__, template_folder='templates')
    try:
        if config:
            app.config.from_object(config)

        app_initializer = Initializer(app)
        app_initializer.init_app()

        return app

    except Exception as e:
        logger.exception("初始化APP失败 %s" % str(e))
        raise e





