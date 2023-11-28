from celery import Celery

app = Celery('pcs_celery')

class BaseConfig:

    broker_connection_retry_on_startup = True


class DevConfig(BaseConfig):
    broker_url = 'redis://192.168.3.99:6379/0'
    result_backend = 'redis://192.168.3.99:6379/2'

class ProdConfig(BaseConfig):
    broker_url = 'redis://192.168.3.99:6379/0'
    result_backend = 'redis://192.168.3.99:6379/2'

app.config_from_object(DevConfig)
app.autodiscover_tasks(['pcs.video'], force=True)


@app.task(name='ad_add')
def ad_add():
    import logging
    raise Exception("111")
    logging.getLogger(__name__).warning("sdasd")
    return 1+1

a = 1