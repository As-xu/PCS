import logging
import os

logger = logging.getLogger(__name__)

from pcs.common.Initializer import Initializer
from pcs.base.BaseFlaskApp import BaseFlaskApp


def create_app(config=None):
    app = BaseFlaskApp(__name__, template_folder='templates')
    try:
        # config_module = os.environ.get("PCS_CONFIG", "pcs.config")

        if config:
            app.config.from_object(config)

        app_initializer = Initializer(app)
        app_initializer.init_app()

        return app

    except Exception as e:
        logger.exception("初始化APP失败 %s" % str(e))
        raise e





