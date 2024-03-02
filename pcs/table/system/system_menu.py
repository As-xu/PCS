from pcs.common.base import BaseTable


class SystemMenuTable(BaseTable):
    table_name = "system_menu_list"

    def user_login(self, user_id):
        select_sql = """
            select *
              from 
        """
        return self._query(select_sql)