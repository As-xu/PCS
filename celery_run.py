from pcs.extensions.celery_extension import pcs_celery_app

if __name__ == '__main__':
    pcs_celery_app.start()