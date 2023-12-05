workers = 6
threads = 3
bind = '0.0.0.0:8080'
daemon = True
worker_class = 'gevent'
worker_connections = 2000
pidfile = '/home/PCS/gunicorn.pid'
accesslog = '/home/PCS/log/gunicorn_acess.log'
errorlog = '/home/PCS/log/gunicorn_error.log'
loglevel = 'info'