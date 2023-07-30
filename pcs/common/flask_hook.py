from flask import request, current_app
import logging

logger = logging.getLogger(__name__)


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
