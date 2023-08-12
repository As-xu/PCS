import psycopg2
import psycopg2.extensions
from psycopg2.extras import RealDictCursor
import logging


logger = logging.getLogger(__name__)


class LoggingCursor(psycopg2.extensions.cursor):
    def execute(self, sql, args=None):

        try:
            psycopg2.extensions.cursor.execute(self, sql, args)
        except Exception as exc:
            logger.error("%s: %s" % (exc.__class__.__name__, exc))
            raise


class LoggingRealDictCursor(RealDictCursor):
    def execute(self, sql, args=None):
        try:
            psycopg2.extensions.cursor.execute(self, sql, args)
        except Exception as exc:
            logger.error("%s: %s" % (exc.__class__.__name__, exc))
            raise


class DBPool(dict):
    def __init__(self, *args, **kwargs):
        super(DBPool, self).__init__(*args, **kwargs)

    def exists_pool(self, pool_name):
        return True if pool_name in self.keys() else False

