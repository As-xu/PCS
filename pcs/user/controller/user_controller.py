from pcs.common.base import BaseController
from pcs.common.sql_condition import Sc
from pcs.common.response import Response
from pcs.common.enum.user_enum import UserType
from pcs.common.enum.common_enum import LogType
from pcs.utils.password import check_password, encrypt_password
from flask_jwt_extended import create_access_token, set_access_cookies, unset_access_cookies
import logging


logger = logging.getLogger(__name__)


class UserController(BaseController):
    def user_login(self, request_data):
        username = request_data.get("user_name")
        password = request_data.get("password")
        user_t = self.get_table_obj('UserTable')
        user_login_t = self.get_table_obj('UserLoginTable')

        sc = Sc([("name", "=", username)])
        user_result = user_t.query(sc, fields=["id", "password"])
        if not user_result:
            return Response.error("没有此用户'{0}'".format(username))

        user_info = user_result[0]
        hash_password = user_info.get("password")
        user_id = user_info.get("id")
        is_valid = check_password(password, hash_password)
        if is_valid:
            return Response.error("用户名或者密码错误")

        user_login_t.user_login()

        access_token = create_access_token(identity={"user_id": user_id, "user_name": username})
        response = Response.success("登录成功!")
        set_access_cookies(response, access_token)
        return response

    def user_register(self, request_data):
        self.close_autocommit()
        user_t = self.get_table_obj('UserTable')
        user_log_t = self.get_table_obj('UserLogTable')

        username = request_data.get("user_name")
        password = request_data.get("password")
        phone = request_data.get("phone") or ""
        email = request_data.get("email") or ""

        sc = Sc([("name", "=", username)])
        user_result = user_t.query(sc, fields=["id", "password"])
        if user_result:
            return Response.error("已存在相同用户名")

        hash_password = encrypt_password(password)

        user_data = {
            "name": username, "password": hash_password, "active": True,
            "phone": phone, "email": email, "show_name": username, "user_type": UserType.guest.value,
        }
        user_result = user_t.create(user_data)

        user_id = user_result.get("id")
        user_log_t.add_user_log(user_id, LogType.Create.value, "创建用户[{0}]成功".format(username))
        self.commit()
        return Response.success()

    def user_logout(self):
        user_login_t = self.get_table_obj('UserLoginTable')
        user_login_t.user_logout()

        response = Response.success()
        unset_access_cookies(response)
        return response
