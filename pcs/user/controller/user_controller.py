from pcs.common.base import BaseController
from flask_jwt_extended import create_access_token
from flask import current_app, jsonify
from pcs.common import Sc, Response, errors
from hashlib import sha256
import passlib.context
import logging

logger = logging.getLogger(__name__)

DEFAULT_CRYPT_CONTEXT = passlib.context.CryptContext(
    # kdf which can be verified by the context. The default encryption kdf is
    # the first of the list
    ['pbkdf2_sha512', 'plaintext'],
    # deprecated algorithms are still verified as usual, but ``needs_update``
    # will indicate that the stored hash should be replaced by a more recent
    # algorithm. Passlib 1.6 supports an `auto` value which deprecates any
    # algorithm but the default, but Ubuntu LTS only provides 1.5 so far.
    deprecated=['plaintext'],
)


class UserController(BaseController):
    def create_user(self):
        pass

    def user_login(self, request_data):
        # self.close_autocommit()

        username = request_data.get("user_name")
        password = request_data.get("password")
        user_t = self.get_table_obj('UserTable')

        sc = Sc([("name", "=", username)], )
        user_result = user_t.query(sc, fields=["id", "password"])
        if not user_result:
            return Response.error("没有此用户'{0}'".format(username))

        user_info = user_result[0]
        password = user_info.get("password")

        access_token = create_access_token(identity=username)
        return Response.json_data({"access_token": access_token})

    def user_register(self, request_data):
        username = request_data.get("username")
        password = request_data.get("password")
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)