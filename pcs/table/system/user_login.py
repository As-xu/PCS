from pcs.common.base import BaseTable
from pcs.common.enum.user_enum import LoginType
from datetime import datetime


class UserLoginTable(BaseTable):
    table_name = 'user_login_list'

    def user_login(self, user_id):
        self.user_id = user_id
        login_data = {
            "user_id": user_id, "login_type": LoginType.Login.value, "login_time": datetime.now(),
            "login_ip": self.request_ip,
        }
        return self.create(login_data)

    def user_logout(self):
        login_data = {
            "user_id": self.user_id, "login_type": LoginType.Logout.value, "login_time": datetime.now(),
            "login_ip": self.request_ip,
        }
        return self.create(login_data)
