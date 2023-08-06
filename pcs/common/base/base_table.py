from pcs.common.enum.system_enum import DBResultState, DBType, DBExecMode
from psycopg2.errors import Error as PgError
from pcs.common.sql_operator import *
import logging
import datetime
import json

logger = logging.getLogger(__name__)


def reset_state(func):
    def reset(*args, **kwargs):
        return func(*args, **kwargs)

    return reset


class TableInfo:
    def __init__(self, table):
        self.__table = table


class Tables:
    def __init__(self):
        self.__tables = {}

    @property
    def tables(self):
        return self.__tables

    def add_table(self, table_class):
        if not issubclass(table_class, BaseTable):
            raise Exception("%s: 不是一个Table 类" % str(table_class))

        if self.exists_table(table_class.__name__):
            return None
        self.__tables[table_class.__name__] = table_class

    def exists_table(self, table_name):
        if table_name in self.__tables.keys():
            return True

        return False

    def get_table(self, table_name, conn):
        if not self.exists_table(table_name):
            raise Exception("不存在此Table %s" % table_name)

        table_class = self.__tables.get(table_name)
        return table_class(conn)


class BaseTable(object):
    db_name = None
    db_type = None
    table_name = None
    default_value = {}
    primary_keys = ("id",)

    def __init__(self, cur, user_id=None):
        self.cur = cur
        self.user_id = user_id
        self.user_id = 1
        self.__log_field = True

        self.exec_state = ExecuteState()

    @property
    def field_symbol(self):
        if self.db_type == DBType.Postgresql.value:
            return '"'
        return ''

    @property
    def table_field_sql(self):
        if self.db_type == DBType.Postgresql.value:
            return '"'
        return ''

    @property
    def like_operate(self):
        if self.db_type == DBType.Postgresql.value:
            return 'ilike'
        return 'like'

    @property
    def regex_operate(self):
        if self.db_type == DBType.Postgresql.value:
            return 'regexp'
        return '~'

    @property
    def not_regex_operate(self):
        if self.db_type == 'regexp':
            return 'not regexp'
        return '!~'

    @property
    def exec_success(self):
        return self.exec_state.state == DBResultState.SUCCESS.value

    @property
    def exec_failure(self):
        return self.exec_state.state == DBResultState.FAILURE.value

    @property
    def error_msg(self):
        return self.exec_state.error_msg

    def get_table_name_sql(self):
        return ' {0}{1}{0} '.format(self.field_symbol, self.table_name)

    def get_table_field_sql(self, field):
        return ' {0}{1}{0} '.format(self.field_symbol, field)

    def query(self, sc, fields=None, offset=None, limit=None, order_by=None, count=None, distinct=None):
        sql_str, params = self._generate_query_sql(sc, fields=fields, offset=offset, limit=limit,
                                                   order_by=order_by, count=count, distinct=distinct)
        if not sql_str:
            self.exec_state.failure('生成SQL失败')
            return None

        return self._query(sql_str, params=params)

    def _query(self, sql_str, params=None):
        rows = self.__execute(sql_str, params=params)
        return rows

    def create(self, insert_data):
        if not insert_data:
            self.exec_state.failure("创建内容为空")
            return None

        insert_sql, params = self._generate_insert_sql(insert_data)

        if not insert_sql:
            self.exec_state.failure('生成SQL失败')
            return None

        return self._create(insert_sql, params=params)

    def create_no_log(self, insert_dict):
        old_log_field, self.__log_field = self.__log_field, False
        result = self.create(insert_dict)
        self.__log_field = old_log_field
        return result

    def _create(self, sql_str, params=None):
        return self.__execute(sql_str, params=params, mode=DBExecMode.INSERT.name)

    def delete(self, condition):
        if not condition:
            self.exec_state.failure("未设定删除条件")
            return None

        delete_sql, params = self._generate_delete_sql(condition)

        if not delete_sql:
            self.exec_state.failure('生成SQL失败')
            return None

        return self._delete(delete_sql, params=params)

    def _delete(self, delete_sql, params=None):
        rowcount = self.__execute(delete_sql, params=params, mode=DBExecMode.INSERT.name)
        if not rowcount:
            self.exec_state.no_change("未删除任何内容")

        return None

    def write(self, update_dict, condition):
        if not update_dict:
            self.exec_state.failure("更新内容为空")
            return None

        if not condition:
            self.exec_state.failure("更新未设定条件")
            return None

        update_sql, params = self._generate_update_sql(update_dict, condition)
        if not update_sql:
            self.exec_state.failure("更新未设定条件")
            return None

        return self._write(update_sql, params=params)

    def _write(self, update_sql, params=None):
        rowcount = self.__execute(update_sql, params=params, mode=DBExecMode.UPDATE.name)
        if not rowcount:
            self.exec_state.no_change("未更新任何内容")

        return None

    def batch_write(self, update_data_list, condition_keys=None, data_keys=None, page_size=1000, fetch=False,
                    field_type=None):
        pass
        """
        :param update_data_list:
        :param update_key_list：指定更新数据的条件key
        :param page_size：每次执行数量
        :param fetch：是否抓取返回值
        :param field_type：指定每个键的数据类型, 针对部分情况下, 存在所有数值为None值时使用,支持 浮点数, 整数,bool值, 时间,日期, JSON
        {
            "int":["int_field"],
            "float": ["float_field"],
            "bool":["bool_field"],
            "datetime":["datetime_field"],
            "date":["datetime_field"],
            "json":["json_field"],
        }
        :return:
        """
        if not update_data_list:
            return True

        data_keys = data_keys if data_keys else update_data_list[0].keys()
        for update_dict in update_data_list:
            if data_keys != update_dict.keys():
                self.exec_state.failure("更新的字段不一致")
                return None

        update_sql, params, template = self._generate_batch_update_sql(update_data_list, data_keys,
                                                                       condition_keys=condition_keys,
                                                                       field_type=field_type)
        if not update_sql:
            self.exec_state.failure("生成SQL失败")
            return None

        return self._batch_write(update_sql, params=params, template=template, page_size=page_size, fetch=fetch)

    def _batch_write(self, update_sql, params=None, template=None, page_size=1000, fetch=True):
        rowcount = self.__execute(update_sql, params=params, template=template, page_size=page_size, fetch=fetch)
        if not rowcount:
            self.exec_state.no_change("未更新任何内容")

        return True

    def _get_permissions_condition(self):
        return True, []

    def _generate_query_field_sql(self, fields=None, distinct=False):
        if not fields:
            fields = []

        sql_query_fields = []
        for f in fields:
            sql_query_fields.append('{symbol}{fields}{symbol}'.format(symbol=self.field_symbol, fields=f))

        field_sql = ','.join(sql_query_fields)

        if not field_sql:
            field_sql = " * "

        if distinct and fields:
            field_sql = " distinct " + field_sql

        return field_sql

    def _generate_query_sql(self, sc, fields=None, offset=None, limit=None, order_by=None, count=None,
                            distinct=None):
        success, permissions_condition = self._get_permissions_condition()
        if not success:
            return False, None

        sc.add_conditions(permissions_condition)

        field_sql = self._generate_query_field_sql(fields, distinct)
        condition_sql, paras = self.__generate_condition_sql(sc)

        select_sql = """
            select {field_sql}
              from {table_name}
             where 1 = 1
                   {condition_sql}
        """.format(
            table_name=self.get_table_name_sql(),
            field_sql=field_sql,
            condition_sql=condition_sql,
        )

        if not count and order_by:
            select_sql += " Order By {order_by}".format(order_by=order_by)

        if isinstance(offset, int):
            select_sql += " Offset {offset}".format(offset=offset)

        if isinstance(limit, int):
            select_sql += " Limit {limit}".format(limit=limit)

        if count:
            select_sql = " select count(1) count from ({select_sql}) t".format(select_sql=select_sql)

        return select_sql, paras

    def __done_special_query_condition(self, conditions):
        if not conditions:
            return []

        new_conditions = []
        for condition in conditions:
            query_name = condition.get(SQL_QUERY_FIELD)
            operate = condition.get(SQL_QUERY_OPERATE)
            value = condition.get(SQL_QUERY_VALUE)

            if operate.startswith('in_or_') and operate.endswith('like'):
                operate = operate.replace('in_or_', '')
                if value.find(",") != -1:
                    value_list = value.split(",")
                else:
                    value_list = [value]

                if len(value_list) > 1:
                    for index in range(0, len(value_list) - 1):
                        new_conditions.append({SQL_QUERY_FIELD: "", SQL_QUERY_OPERATE: SQL_OR, SQL_QUERY_VALUE: ""})

                for item in value_list:
                    new_conditions.append(
                        {SQL_QUERY_FIELD: query_name, SQL_QUERY_OPERATE: operate, SQL_QUERY_VALUE: item})
            elif operate.startswith('in_or_'):
                if value.find(",") != -1:
                    value = value.split(",")
                    operate = "in"
                else:
                    operate = operate.replace('in_or_', '')

                new_conditions.append({SQL_QUERY_FIELD: query_name, SQL_QUERY_OPERATE: operate, SQL_QUERY_VALUE: value})
            else:
                new_conditions.append(condition)

        return new_conditions

    def __generate_condition_sql(self, sc):
        conditions = sc.condition
        conditions = self.__done_special_query_condition(conditions)

        like_operate = self.like_operate
        regex_operate = self.regex_operate
        not_regex_operate = self.not_regex_operate

        sql_condition_list = []
        sql_condition_value_list = []
        operate_or_count = 0
        operate_or_used_count = 0
        for condition in conditions:
            field = condition.get(SQL_QUERY_FIELD)
            operate = condition.get(SQL_QUERY_OPERATE)
            value = condition.get(SQL_QUERY_VALUE)

            if isinstance(field, str):
                fields = [field]
            elif isinstance(field, list):
                fields = field
            else:
                continue

            if operate not in SQL_QUERY_OPERATE_VALUES:
                continue
                # raise Exception("未知的操作符'{operate}'".format(operate=operate))

            if operate == SQL_OR:
                if operate_or_count == 0:
                    operate_or_count += 2
                else:
                    operate_or_count += 1
                continue

            lower_operate = operate.lower()
            fields_sql_list = []
            for f in fields:
                field_str = self.get_table_field_sql(f)
                if 'llike' == lower_operate:
                    operate_str = like_operate
                    sql_condition_value_list.append("%" + value)
                elif lower_operate in ('like', 'ilike'):
                    operate_str = like_operate
                    sql_condition_value_list.append("%" + value + "%")
                elif 'rlike' == lower_operate:
                    operate_str = like_operate
                    sql_condition_value_list.append(value + "%")
                elif lower_operate in ('not like', 'not ilike'):
                    operate_str = ' not ' + like_operate
                    sql_condition_value_list.append("%" + value + "%")
                elif 'regular_exp' == lower_operate:
                    operate_str = regex_operate
                    sql_condition_value_list.append(value)
                elif 'not regular_exp' == lower_operate:
                    operate_str = not_regex_operate
                    sql_condition_value_list.append(value)
                elif 'null' == lower_operate:
                    operate_str = 'is null'
                elif 'not null' == lower_operate:
                    operate_str = 'is not null'
                elif lower_operate in ('in', 'not in'):
                    operate_str = lower_operate
                    if isinstance(value, str):
                        value = eval(value)
                    sql_condition_value_list.append(tuple(value))
                else:
                    operate_str = operate
                    sql_condition_value_list.append(value)

                fields_sql_list.append(" {0} {1} %s ".format(field_str, operate_str))

            if operate_or_count > 0 and operate_or_used_count == 0:
                sql_condition = " And (("
            elif operate_or_count > 0:
                sql_condition = " Or ("
            else:
                sql_condition = " And ("

            sql_condition += " or ".join(fields_sql_list)
            sql_condition += ")"

            if operate_or_count > 0:
                operate_or_used_count += 1
                operate_or_count -= 1

                if operate_or_count == 0:
                    operate_or_used_count = 0

                    sql_condition += ")"

            sql_condition_list.append(sql_condition)

        if operate_or_count > 0:
            sql_condition_list.append(")")

        condition_sql = ''
        paras = None

        if sql_condition_list:
            condition_sql = str.join(' ', sql_condition_list)
            paras = tuple(sql_condition_value_list)

        return condition_sql, paras

    def paginate_query(self, condition, page_index=1, page_size=20, fields=None, order_by=None):
        sql_str, params = self._generate_query_sql(condition, fields=fields, order_by=order_by)
        if not sql_str:
            self.exec_state.failure('生成SQL失败')
            return None

        return self._paginate_query(sql_str, params=params, page_index=page_index, page_size=page_size)

    def _paginate_query(self, sql_str, params=None, page_index=1, page_size=20):
        query_row_count_sql = """
            select count(1) row_count 
              from ({0}) t
             where 1=1
        """.format(sql_str)

        rows = self.__execute(query_row_count_sql, params=params)
        row_count = 0

        if row_count <= (page_index - 1) * page_size:
            page_index = 1

        offset = (page_index - 1) * page_size
        limit = page_size
        query_sql = """
            select * 
              from (
                    {sql_str}
                   ) t 
             limit {limit}
            offset {offset}
        """.format(
            sql_str=sql_str,
            limit=limit,
            offset=offset,
        )

        return row_count, self.__execute(query_sql, params=params)

    def __execute(self, sql_str, params=None, mode=DBExecMode.QUERY.name, **kwargs):
        result = None
        self.exec_state.reset_state()
        try:
            if mode == DBExecMode.BATCH_UPDATE.name:
                pass
            elif mode == DBExecMode.BATCH_INSERT.name:
                pass

            self.cur.execute(sql_str, params)
            if mode == DBExecMode.QUERY.name:
                result = self.cur.fetchall()
            elif mode == DBExecMode.UPDATE.name:
                result = self.cur.rowcount
            elif mode == DBExecMode.INSERT.name:
                result = self.cur.fetchone()
            elif mode == DBExecMode.DELETE.name:
                result = self.cur.rowcount
        except PgError as e:
            self.exec_state.failure("DB执行SQL失败'{0}'".format(str(e)))
        except Exception as e:
            self.exec_state.failure("执行失败'{0}'".format(str(e)))

        return result

    def mogrify(self, sql_str, params=None):
        return self.cur.mogrify(sql_str, params)

    def get_tables_info(self, table_names):
        select_sql = """
           select col.table_schema schema_name,
                  col.table_name,
                  col.column_name,
                  col.is_nullable,
                  col.data_type col_type,
                  col.udt_name,
                  pc.oid, 
                  col.ordinal_position,
                  COALESCE((SELECT col.ordinal_position = ANY ( conkey ) 
                              FROM pg_constraint 
                             WHERE contype = 'p' AND conrelid = pc.oid 
                             ), FALSE ) is_primarykey,
                  col_description(pc.oid, col.ordinal_position) column_comment
             from information_schema.columns col
        left join pg_namespace ns on ns.nspname = col.table_schema
        left join pg_class pc on col.table_name = pc.relname and pc.relnamespace = ns.oid 
            where col.table_name in %s
            order by col.table_schema, col.table_name, col.ordinal_position
        """
        return self._query(select_sql, (table_names,))

    def get_self_table_info(self):
        return self.get_tables_info([self.table_name])

    def _generate_insert_sql(self, insert_data):
        insert_fields = []
        insert_paras = []
        parameter_list = []

        self.__remove_extra_field(insert_data)
        self.__add_extra_value(insert_data)

        if self.db_type == DBType.Postgresql.value and self.primary_keys:
            insert_fields.append(self.primary_keys[0])
            insert_paras.append("nextval('%s_id_seq')" % self.table_name)

        for key in insert_data.keys():
            insert_fields.append(key)
            insert_paras.append('%s')

            field_value = insert_data[key]
            if isinstance(field_value, (dict, list)):
                field_value = json.dumps(field_value)

            parameter_list.append(field_value)

        if not insert_fields:
            return False, False

        fields_sql = ",".join(self.get_table_field_sql(field) for field in insert_fields)
        params_sql = ",".join(insert_paras)
        return_sql = ""
        if self.primary_keys and self.db_type == DBType.Postgresql.value:
            return_sql = ' Returning "%s" ' % '","'.join(self.primary_keys)

        insert_sql = """
            Insert Into {table_name} (
                {fields_sql}
            )
            Values(
                {params_sql}
            )
            {return_sql}
        """.format(
            table_name=self.get_table_name_sql(),
            fields_sql=fields_sql,
            params_sql=params_sql,
            return_sql=return_sql,
        )

        return insert_sql, tuple(parameter_list)

    def __add_extra_value(self, value_dict, mode=DBExecMode.INSERT.name):
        if mode == DBExecMode.INSERT.name:
            if self.__log_field:
                value_dict.update({
                    'write_date': datetime.datetime.utcnow(),
                    'write_uid': self.user_id,
                    'create_date': datetime.datetime.utcnow(),
                    'create_uid': self.user_id,
                })

            for key in self.default_value.keys():
                if key in value_dict.keys():
                    continue

                value_dict[key] = self.default_value[key]
        elif mode == DBExecMode.UPDATE.name:
            if self.__log_field:
                value_dict.update({
                    'write_date': datetime.datetime.utcnow(),
                    'write_uid': self.user_id,
                })

    def __remove_extra_field(self, value_dict):
        value_dict.pop(SAVE_FLAG, None)

    def _generate_update_sql(self, update_data=None, condition=None):
        self.__remove_extra_field(update_data)
        self.__add_extra_value(update_data)

        set_sql_list = []
        params = []
        for field_name, field_value in update_data.items():
            if isinstance(field_value, (dict, list)):
                field_value = json.dumps(field_value)

            set_sql = self.get_table_field_sql(field_name) + ' = %s '
            set_sql_list.append(set_sql)
            params.append(field_value)

        where_sql, where_params = self.__generate_condition_sql(condition)

        if not set_sql_list:
            self.error_message = "未设置更新内容"
            return None, None

        if not where_sql:
            self.error_message = "未设置更新条件"
            return None, None

        params.extend(where_params)

        update_sql = """
            update {table_name}
               set {set_sql}
             where 1=1
                   {where_sql}
        """.format(
            table_name=self.get_table_name_sql(),
            set_sql=','.join(set_sql_list),
            where_sql=where_sql,
        )
        return update_sql, tuple(params)

    def _generate_batch_update_sql(self, update_data_list, data_keys, condition_keys=None, field_type=None):
        if not field_type:
            field_type = {}

        data_list = []
        for update_data in update_data_list:
            self.__remove_extra_field(update_data)
            self.__add_extra_value(update_data)

            update_data_list = []
            for key in data_keys:
                value = update_data.get(key)
                if isinstance(update_data.get(key), (dict, list)):
                    value = json.dumps(update_data.get(key))
                update_data_list.append(value)

            data_list.append(tuple(update_data_list))

        if not condition_keys:
            condition_keys.extend(self.primary_keys)

        set_sql_list = []
        where_sql_list = []

        for key in data_keys:
            key_sql = self.get_table_field_sql(key)
            if key in condition_keys:
                where_sub_sql = ' And {0}.{1} = dt.{1} '.format(self.get_table_name_sql(), key_sql)
                where_sql_list.append(where_sub_sql)
            else:
                set_sql = ' {0} = dt.{0} '.format(key_sql)
                set_sql_list.append(set_sql)

        if not set_sql_list:
            self.error_message = "未设置更新内容"
            return False, False, False

        if not where_sql_list:
            self.error_message = "未设置更新条件"
            return False, False, False

        key_sql = ','.join(self.get_table_field_sql(key) for key in data_keys)
        update_sql = """
            update {table_name}
               set {set_sql}
              from (values %s) as dt ({key_sql})
             where 1=1
               and {where_sql}
        """.format(
            table_name=self.get_table_name_sql(),
            set_sql=','.join(set_sql_list),
            key_sql=key_sql,
            where_sql=' '.join(where_sql_list),
        )

        type_dict = {
            f: '::' + SQL_TYPE_MAP.get(data_type)
            for data_type in field_type.keys()
            for f in (field_type.get(data_type) or []) if data_type in SQL_TYPE_MAP.keys()
        }
        template = '(' + ','.join('%s' + (type_dict.get(key) or '') for key in data_keys) + ')'

        return update_sql, data_list, template

    def _generate_group_by_select_sql(self, src_select_sql, group_by, query_name_list=[], show_name_list=None):
        pass

    #     if not show_name_list:
    #         show_name_list = query_name_list

    #     group_by = self.__deal_multi_column_group_by(group_by)

    #     group_name_list = [item for item in group_by]
    #     need_group_name_list = [item for item in group_by if item.get("is_group")]

    #     group_by_str = ""
    #     new_query_name_list, new_show_name_list = [], []
    #     if not need_group_name_list:
    #         for query_name in query_name_list:
    #             if query_name in group_name_list:
    #                 continue

    #             old_group_name_list, new_group_name_list, show_names_list = self.__get_new_group_name([query_name],
    #                                                                                                   query_name_list,
    #                                                                                                   show_name_list)

    #             for old_group_name in old_group_name_list:
    #                 new_query_name_list.append(old_group_name)
    #                 new_show_name_list.append(show_names_list[old_group_name_list.index(old_group_name)])
    #     else:
    #         group_name_list = [need_group_name.get("group_name") for need_group_name in need_group_name_list]

    #         old_group_name_list, new_group_name_list, show_names_list = self.__get_new_group_name(group_name_list,
    #                                                                                               query_name_list,
    #                                                                                               show_name_list)
    #         for new_group_name in new_group_name_list:
    #             new_query_name_list.append(new_group_name)
    #             new_show_name_list.append(show_names_list[new_group_name_list.index(new_group_name)])

    #         new_query_name_list.append("count(1)")
    #         new_show_name_list.append("cnt")

    #         group_by_str = " Group by %s" % str.join(",", new_group_name_list)

    #         for need_group_name in need_group_name_list:
    #             for item in need_group_name.get("aggregate_column",[]):
    #                 new_query_name_list.append('%s' % (item.get("aggregate_function")))
    #                 new_show_name_list.append(item.get("name"))

    #     sql_query_name_list = []
    #     for index in range(len(new_query_name_list)):
    #         sql_query_name_list.append('%s %s%s%s' % (new_query_name_list[index], self.__join_char,
    #                                                   new_show_name_list[index], self.__join_char))

    #     select_sql = """
    #                 select %s
    #                   from (%s) t
    #                  where 1 = 1
    #                   %s
    #                    """ % (str.join(',', sql_query_name_list), src_select_sql, group_by_str)

    #     return select_sql

    def __get_new_group_name(self, group_name_list, query_name_list, show_name_list):
        pass

    #     old_group_name_list, new_group_name_list, show_names_list = [], [], []

    #     for group_name in group_name_list:
    #         if ":" in group_name:
    #             split_array = group_name.split(':')
    #             old_group_name = split_array[0]
    #             date_part = split_array[1]
    #             date_type = split_array[2] if len(split_array) == 3 else 'date'

    #             if date_type == "datetime":
    #                 if date_part == "year":
    #                     new_group_name = "date_part('%s', %s + interval '%s hours')" % (date_part, old_group_name, self.tz)
    #                 elif date_part == 'day':
    #                     new_group_name = "to_char(%s + interval '%s hours', 'yyyy-MM-dd')" % (old_group_name, self.tz)
    #                 else:
    #                     new_group_name = "cast(date_part('year', %s + interval '%s hours') as varchar(4)) || '-' || lpad(cast(date_part('%s', %s + interval '%s hours') as varchar(2)), 2, '0')" % (
    #                     old_group_name, self.tz, date_part, old_group_name, self.tz)
    #             else:
    #                 if date_part == "year":
    #                     new_group_name = "date_part('%s', %s)" % (date_part, old_group_name)
    #                 elif date_part == 'day':
    #                     new_group_name = "to_char(%s, 'yyyy-MM-dd')" % (old_group_name)
    #                 else:
    #                     new_group_name = "cast(date_part('year', %s) as varchar(4)) || '-' || lpad(cast(date_part('%s', %s) as varchar(2)), 2, '0')" % (
    #                     old_group_name, date_part, old_group_name)

    #             show_name = "%s:%s" % (show_name_list[query_name_list.index(old_group_name)], date_part)
    #         else:
    #             old_group_name = group_name
    #             new_group_name = group_name
    #             show_name = show_name_list[query_name_list.index(old_group_name)]

    #         old_group_name_list.append(old_group_name)
    #         new_group_name_list.append(new_group_name)
    #         show_names_list.append(show_name)

    #     return old_group_name_list, new_group_name_list, show_names_list

    # def __deal_multi_column_group_by(self, group_by):
    #     new_group_by = []
    #     for group_by_item in group_by:
    #         group_name = group_by_item.get("group_name")
    #         is_group = group_by_item.get("is_group")
    #         if not is_group:
    #             new_group_by.append(group_by_item)
    #             continue

    #         if "," not in group_name:
    #             new_group_by.append(group_by_item)
    #             continue

    #         multi_columns = group_name.split(",")
    #         for group_column in multi_columns:
    #             exists_group_by = [item for item in group_by if item.get("group_name") == group_column.strip()]
    #             if exists_group_by:
    #                 exists_group_by[0].update({"is_group": True})
    #             else:
    #                 new_item = group_by_item.copy()
    #                 new_item.update({"group_name": group_column.strip()})

    #                 if multi_columns.index(group_column) != 0:
    #                     new_item.update({"aggregate_column": []})

    #                 new_group_by.append(new_item)

    #     return new_group_by

    def _generate_delete_sql(self, condition):
        condition_sql, paras = self.__generate_condition_sql(condition)

        delete_sql = """
                    delete from {table_name}
                     where 1= 1 
                     {condition_sql}
                """.format(
            table_name=self.table_name,
            condition_sql=condition_sql,
        )
        return delete_sql, paras

    def batch_create(self, insert_value_list=None, page_size=1000, fetch=False):
        pass

    #     if not insert_value_list:
    #         return True

    #     data_keys = insert_value_list[0].keys()
    #     if not data_keys:
    #         self.error_code = Global.response_error_code
    #         self.error_message = 'insert value is empty'
    #         return False

    #     if any(value_dict.keys() != data_keys for value_dict in insert_value_list):
    #         self.error_code = Global.response_error_code
    #         self.error_message = 'insert value key is not same'
    #         return False

    #     value_iter = (self.__initial_add_data(value_data) for value_data in insert_value_list)

    #     insert_sql, parameter_list, template = self._generate_batch_insert_sql(value_iter)

    #     if not insert_sql:
    #         self.error_code = Global.response_error_code
    #         self.error_message = 'generate insert sql error'
    #         return False

    #     result = self._batch_create(insert_sql, paras=parameter_list, template=template, page_size=page_size,
    #                                 fetch=fetch)
    #     if self.error_code == Global.response_error_code:
    #         return result

    #     return result

    def _batch_create(self, insert_sql, paras=None, template=None, page_size=1000, fetch=True):
        pass
    #     paras = paras if not paras else tuple(paras)

    #     result = self._psqlOperate.execute_batch_create_scalar(insert_sql, parameters=paras, template=template, page_size=page_size, fetch=fetch)
    #     if self._psqlOperate.exists_error:
    #         self.error_code = Global.response_error_code
    #         self.error_message = self._psqlOperate.error_message
    #         return False

    #     if not result:
    #         self.error_code = Global.response_error_code
    #         self.error_message = 'no data add'
    #         return False
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None

    #     return result


class ExecuteState:
    def __init__(self):
        self.state = DBResultState.SUCCESS.value
        self.error_msg = ""

    def failure(self, msg):
        self.state = DBResultState.FAILURE.value
        self.error_msg = msg

    def success(self, msg):
        self.state = DBResultState.SUCCESS.value
        self.error_msg = msg

    def no_change(self, msg):
        self.state = DBResultState.NOCHANGE.value
        self.error_msg = msg

    def reset_state(self):
        self.state = DBResultState.SUCCESS.value
        self.error_msg = ""
