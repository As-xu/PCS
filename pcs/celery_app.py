from celery import Celery

app = Celery('pcs_celery')

class BaseConfig:
    include = [
        'pcs.video.tasks.video_add',
        'pcs.user.tasks',
    ]

    broker_connection_retry_on_startup = True


class DevConfig(BaseConfig):
    broker_url = 'redis://192.168.3.99:6379/0'
    result_backend = 'redis://192.168.3.99:6379/1'

class ProdConfig(BaseConfig):
    broker_url = 'redis://192.168.3.99:6379/0'
    result_backend = 'redis://192.168.3.99:6379/1'


app.config_from_object(DevConfig)

app.conf.update(
    result_expires=3600,
)

