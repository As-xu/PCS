import logging
import sys
logger = logging.getLogger('pcs')

from pcs.initialization import Initializer
from pcs.utils.config_parse import parse_config
from pcs.common.base import BaseFlaskApp
from flask.cli import load_dotenv


def create_app():
    args = sys.argv[1:]
    config = parse_config(args)

    try:
        load_dotenv()
        app = BaseFlaskApp(__name__, template_folder='templates')

        if config:
            app.config.from_mapping(config)

        app_initializer = Initializer(app)
        app_initializer.init_app()

        return app

    except Exception as e:
        logger.exception("初始化PCS失败 %s" % str(e))
        raise e

