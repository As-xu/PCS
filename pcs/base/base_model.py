from flask_sqlalchemy import Model
from flask_sqlalchemy import BaseQuery as SqlalchemyBaseQuery
import logging

logger = logging.getLogger(__name__)


class BaseModel(Model):
    db_engine = None

    def search(self):
        return None

    def paginate_query(self):
        return None

    def delete(self):
        return None

    def update(self):
        return None


class BaseQuery(SqlalchemyBaseQuery):
    pass