import logging
from tts.common.base import BaseController
from tts.common.sql_condition import Sc
from tts.common.response import Response


logger = logging.getLogger(__name__)


class SchedulerController(BaseController):
    def query_scheduler_info(self, request_data):
        return Response.success()

    def change_scheduler_status(self, request_data):
        return Response.success()

    def save_scheduler_job(self, request_data):
        return Response.success()

    def query_all_scheduler_job(self, request_data):
        return Response.success()

    def query_one_scheduler_job(self, request_data):
        return Response.success()

    def change_scheduler_job_status(self, request_data):
        return Response.success()