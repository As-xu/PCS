from flask_sqlalchemy import Model
import logging

logger = logging.getLogger(__name__)


class BaseModel(Model):
    pass