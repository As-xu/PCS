from pcs.common.enum.system_enum import ResponseState
from flask import jsonify
import logging


logger = logging.getLogger(__name__)


class Response(object):

    @staticmethod
    def error(msg):
        return jsonify(code=ResponseState.FAILURE.value, msg=msg, data=None)

    @staticmethod
    def warning(msg):
        return jsonify(code=ResponseState.WARNING.value, msg=msg, data=None)

    @staticmethod
    def success(msg=''):
        return jsonify(code=ResponseState.SUCCESS.value, msg=msg, data=None)

    @staticmethod
    def pagination(page_data, page_index, page_count=None):
        data = {
            "page_index": page_index,
            "page_data": page_data,
            "page_count": page_count if page_count else len(page_data)
        }
        return jsonify(code=ResponseState.SUCCESS.value, msg="", data=data)

    @staticmethod
    def json_data(json_data):
        return jsonify(code=ResponseState.SUCCESS.value, msg="", data=json_data)

    @staticmethod
    def html_data(json_data):
        return jsonify(code=ResponseState.SUCCESS.value, msg="", data=json_data)