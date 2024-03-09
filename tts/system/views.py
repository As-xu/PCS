import logging
from flask import render_template
from flask import request
from tts.system import system_bp as bp
from tts.system.controller.scheduler import SchedulerController

logger = logging.getLogger(__name__)


@bp.route('/query_scheduler_info', methods=["POST"])
def query_scheduler_info():
    json_data = request.json
    c = SchedulerController(request)
    return c.query_scheduler_info(json_data)

@bp.route('/change_scheduler_status', methods=["POST"])
def change_scheduler_status():
    json_data = request.json
    c = SchedulerController(request)
    return c.query_scheduler_info(json_data)

@bp.route('/save_scheduler_job', methods=["POST"])
def save_scheduler_job():
    json_data = request.json
    c = SchedulerController(request)
    return c.query_scheduler_info(json_data)

@bp.route('/query_one_scheduler_job', methods=["POST"])
def query_all_scheduler_job():
    json_data = request.json
    c = SchedulerController(request)
    return c.query_one_scheduler_job(json_data)

@bp.route('/query_all_scheduler_job', methods=["POST"])
def query_all_scheduler_job():
    json_data = request.json
    c = SchedulerController(request)
    return c.query_all_scheduler_job(json_data)

@bp.route('/change_scheduler_job_status', methods=["POST"])
def query_all_scheduler_job():
    json_data = request.json
    c = SchedulerController(request)
    return c.change_scheduler_job_status(json_data)