from pcs.common.response import Response
from flask import request, jsonify, render_template
from datetime import datetime
import logging
import uuid
uuid.uuid1()
logger = logging.getLogger(__name__)


class RequestHook:
    @staticmethod
    def handle_before_first_request():
        logger.info("handle_before_first_request")

    @staticmethod
    def handle_before_request():
        logger.info("handle_before_request")

    @staticmethod
    def handle_after_request(response):
        logger.info("handle_after_request")
        return response

    @staticmethod
    def handle_teardown_request(e):
        logger.info("handle_teardown_request")



def log_exception(e):
    error_info = "异常:{0} {1} [{2}]".format(request.root_url, request.path, request.method)
    logger.error(error_info, exc_info=e)
    return error_info


def save_error_msg(error_info, error_code):
    # redis存储临时的错误信息
    pass


class RequestErrorHandle:
    @staticmethod
    def handle_db_error(e):
        error_info = log_exception(e)
        error_code = "{0}-{1}".format(e.code, uuid.uuid1().time_low)
        save_error_msg(error_info, error_code)
        content = "内部错误:错误代码[{}]".format(error_code)
        if request.mimetype in ("application/json", "application/json-rpc"):
            return Response.error(content), 200
        else:
            return render_template("error.html", content=content)

    @staticmethod
    def handle_500_error(e):
        error_code = "500-{1}".format(e.code, uuid.uuid1().time_low)
        save_error_msg(str(e), error_code)
        content = "内部错误:错误代码[{}]".format(error_code)
        if request.mimetype in ("application/json", "application/json-rpc"):
            return Response.error(content), 200
        else:
            return render_template("error.html", content=content)

