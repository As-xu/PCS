import secrets
from configparser import ConfigParser
import os
import logging


SECRET_KEY = secrets.token_hex()
logger = logging.getLogger(__name__)

# 路径设置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'data')
LOG_DIR = os.path.join(BASE_DIR, 'log')


try:
    pcs_cfg = ConfigParser()
    pcs_cfg.read(os.path.join(BASE_DIR, 'pcs.cfg'))
except Exception as e:
    logger.exception(
        "导入配置文件失败 %s", os.path.join(BASE_DIR, 'pcs.cfg')
    )
    raise

# 数据库配置
SQLALCHEMY_DATABASE_URI = pcs_cfg.get("settings", "db_url")
SQLALCHEMY_POOL_SIZE = 10    # 数据库连接池的大小。默认值 5
SQLALCHEMY_POOL_TIMEOUT = 30  # 指定数据库连接池的超时时间。默认是 10
SQLALCHEMY_POOL_RECYCLE = -1
SQLALCHEMY_MAX_OVERFLOW = 3  # 控制在连接池达到最大值后可以创建的连接数。当这些额外的连接回收到连接池后将会被断开和抛弃
SQLALCHEMY_TRACK_MODIFICATIONS = True  # 追踪对象的修改并且发送信号
SQLALCHEMY_COMMIT_ON_TEARDOWN = False

# 日志配置
LOG_FILE_NAME = "pcs_server.log"
LOG_LEVEL = logging.INFO