from tts.common.base import BaseTable


class SystemMenuTable(BaseTable):
    table_name = "system_menu_list"

    def query_user_menu(self, user_id):
        select_sql = """
            select * from system_menu_list where active = true
        """
        return self._query(select_sql)