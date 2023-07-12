import logging

logger = logging.getLogger(__name__)


class BaseModel(object):
    db_engine = None

    @classmethod
    def search(cls, condition, fields=None, offset=None, limit=None, order_by=None):
        return None

    @classmethod
    def _query(cls, sql, params=None):
        return None

    @classmethod
    def paginate_query(cls):
        return None

    @classmethod
    def delete(cls):
        return None

    @classmethod
    def batch_create(cls):
        return None

    @classmethod
    def update(cls):
        return None

    @classmethod
    def _write(cls):
        return None

