from pcs.common.base import BaseTable


class UserLogTable(BaseTable):
    table_name = 'user_log_list'

    def add_user_log(self, user_id, log_type, log_content):
        log_data = {
            "user_id": user_id, "log_type": log_type,  "log_content": log_content
        }
        return self.create(log_data)
