from pcs.celery_app import app
import logging

logger = logging.getLogger(__name__)

@app.task
def video_add():
    logger.info("execute add")
    return 1+1