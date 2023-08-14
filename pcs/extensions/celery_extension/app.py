from celery import Celery

broker_url = 'redis://192.168.3.99:6379/0'
backend = 'redis://192.168.3.99:6379/0'
app = Celery('pcs_celery', broker=broker_url, backend=backend)

app.conf.update(
    result_expires=3600,
)

