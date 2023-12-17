from pcs.celery_app import app
from celery.utils.log import get_task_logger
import time


logger = get_task_logger(__name__)

@app.task(name='tasks.video_add')
def video_add():

    return 1+1