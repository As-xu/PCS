import logging

logger = logging.getLogger(__name__)


class BaseModel(object):
    __db_name = None
    __table_name = None

    @classmethod
    @property
    def table_name(cls):
        return cls.__table_name

    def search(self, domain, fields=None, offset=None, limit=None, order_by=None, is_distinct=None):
        return None

    def _query(self, sql, params=None):
        return None

    def paginate_query(self):
        return None

    def _paginate_query(self, sql, params=None):
        return None

    def delete(self):
        return None

    def batch_create(self):
        return None

    def update(self):
        return None

    def _write(self):
        return None

