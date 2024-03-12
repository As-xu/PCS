from tts.common.enum.system_enum import ResponseState
from flask import jsonify
from flask import Response as FlaskResponse
import logging


logger = logging.getLogger(__name__)


class Response(object):

    @staticmethod
    def error(msg, debug=None):
        return jsonify(code=ResponseState.FAILURE.value, msg=msg, data=None, debug=debug)

    @staticmethod
    def warning(msg, debug=None):
        return jsonify(code=ResponseState.WARNING.value, msg=msg, data=None, debug=debug)

    @staticmethod
    def success(msg='', debug=None):
        return jsonify(code=ResponseState.SUCCESS.value, msg=msg, data=None, debug=debug)

    @staticmethod
    def pagination(page_data, page_index, page_count=None, debug=None):
        data = {
            "page_index": page_index,
            "page_data": page_data,
            "page_count": page_count if page_count else len(page_data)
        }
        return jsonify(code=ResponseState.SUCCESS.value, msg="", data=data, debug=debug)

    @staticmethod
    def json_data(json_data, debug=None):
        return jsonify(code=ResponseState.SUCCESS.value, msg="", data=json_data, debug=debug)

    @staticmethod
    def html_data(data, status=None, headers=None, mimetype=None, content_type=None):
        return FlaskResponse(data, status=status, headers=headers, mimetype=mimetype, content_type=content_type)