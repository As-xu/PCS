import logging
import sys
logger = logging.getLogger('tts')

from tts.initialization import Initializer
from tts.utils.config_parse import parse_config
from tts.common.base import BaseFlaskApp
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
        logger.exception("初始化TTS失败 %s" % str(e))
        raise e

