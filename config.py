import secrets
SECRET_KEY = secrets.token_hex()

#数据库配置
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://pcs:123456@192.168.3.99:5432/pcs_db"
SQLALCHEMY_POOL_SIZE = 10    #数据库连接池的大小。默认值 5
SQLALCHEMY_POOL_TIMEOUT = 30  # 指定数据库连接池的超时时间。默认是 10
SQLALCHEMY_POOL_RECYCLE = -1
SQLALCHEMY_MAX_OVERFLOW = 3  # 控制在连接池达到最大值后可以创建的连接数。当这些额外的连接回收到连接池后将会被断开和抛弃
SQLALCHEMY_TRACK_MODIFICATIONS = True  # 追踪对象的修改并且发送信号
SQLALCHEMY_COMMIT_ON_TEARDOWN = False