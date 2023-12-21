import logging
from flask import render_template
from flask import request
from pcs.video import video_bp as bp
from pcs.video.controller.video import VideoController

logger = logging.getLogger(__name__)


@bp.route('/query_all', methods=["POST"])
def query_all():
    json_data = request.json
    controller = VideoController(request)
    return controller.query_all_video(json_data)


@bp.route('/query_info', methods=["POST"])
def query_info():
    json_data = request.json
    controller = VideoController(request)
    return controller.query_video_info(json_data)


@bp.route('/query_detail', methods=["POST"])
def query_detail():
    json_data = request.json
    controller = VideoController(request)
    return controller.query_video_detail(json_data)


@bp.route('/add', methods=["POST"])
def add():
    json_data = request.json
    controller = VideoController(request)
    return controller.add_video(json_data)

@bp.route('/update_info', methods=["POST"])
def update_info():
    json_data = request.json
    controller = VideoController(request)
    return controller.update_video_info(json_data)

@bp.route('/download_video', methods=["POST"])
def download_video():
    json_data = request.json
    controller = VideoController(request)
    return controller.download_video(json_data)