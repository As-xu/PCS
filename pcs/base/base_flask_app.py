from flask import Flask
import logging

logger = logging.getLogger(__name__)


class BaseFlaskApp(Flask):
    pass