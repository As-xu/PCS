from celery import Celery

broker_url = 'redis://192.168.3.99:6379/0'
backend = 'redis://192.168.3.99:6379/0'
pcs_celery_app = Celery('pcs_celery', broker=broker_url, backend=backend, include=['celery_demo.tasks'])

pcs_celery_app.conf.update(
    result_expires=3600,
)

