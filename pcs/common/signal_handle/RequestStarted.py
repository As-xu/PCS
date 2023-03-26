from flask.signals import request_started
import logging

logger = logging.getLogger(__name__)

@q
@request_started.connect
def test(sender, **extra):
    logger.error("asds")