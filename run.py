from pcs import create_app


def gevent_run():
    from gevent.pywsgi import WSGIServer
    from gevent import monkey
    monkey.patch_all()
    WSGIServer(("127.0.0.1", 5000), create_app()).serve_forever()


def gevent_gunicorn_run():
    import multiprocessing

    # https://j519lee.blog.csdn.net/article/details/129636561
    """gunicorn+gevent 的配置文件"""
    # 预加载资源
    preload_app = True
    # 绑定
    bind = "0.0.0.0:5000"
    # 进程数
    workers = multiprocessing.cpu_count() * 2 + 1
    # 线程数
    threads = multiprocessing.cpu_count() * 2
    # 等待队列最大长度,超过这个长度的链接将被拒绝连接
    backlog = 2048
    # 工作模式
    # worker_class = "egg:meinheld#gunicorn_worker"
    worker_class = "gevent"
    # 最大客户客户端并发数量,对使用线程和协程的worker的工作有影响
    worker_connections = 1200
    # 进程名称
    proc_name = 'gunicorn.pid'
    # 进程pid记录文件
    pidfile = 'app_run.log'
    # 日志等级
    loglevel = 'debug'
    # 日志文件名
    logfile = 'debug.log'
    # 访问记录
    accesslog = 'access.log'
    # 访问记录格式
    access_log_format = '%(h)s %(t)s %(U)s %(q)s'
    # 运行方式 命令行
    # gunicorn - c gunicorn_config.py flask_server: app


def simple_run():
    create_app().run(load_dotenv=True)


if __name__ == '__main__':
    simple_run()


