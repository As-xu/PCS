from pcs.common.enum.system_enum import DBResultState
from psycopg2.errors import Error as PgError
from pcs.common.sql_operator import *
import logging

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

    def __init__(self, cur):
        self.cur = cur
        self.exec_state = ExecuteState()

    # @property
    # def table_name(self):
    #     return self.__class__.__table_name
    #
    # @classmethod
    # @property
    # def db_type(cls):
    #     return cls.__db_type
    #
    # @classmethod
    # def set_db_type(cls, value):
    #     cls.__db_type = value
    #
    # @classmethod
    # @property
    # def db_name(cls):
    #     return cls.__db_name
    #
    # @classmethod
    # def set_db_name(cls, value):
    #     cls.__db_name = value

    @property
    def field_symbol(self):
        if self.db_type == 'postgresql':
            return '"'
        return ''

    @property
    def like_operate(self):
        if self.db_type == 'postgresql':
            return 'ilike'
        return 'like'

    @property
    def regex_operate(self):
        if self.db_type == 'postgresql':
            return 'regexp'
        return '~'

    @property
    def not_regex_operate(self):
        if self.db_type == 'regexp':
            return 'not regexp'
        return '!~'

    def _get_permissions_condition(self):
        return True, []

    def query(self, sc, fields=None, offset=None, limit=None, order_by=None, count=None, distinct=None):
        sql_str, params = self._generate_query_sql(sc, fields=fields, offset=offset, limit=limit,
                                                   order_by=order_by, count=count, distinct=distinct)
        if not sql_str:
            self.exec_state.failure('生成SQL失败')
            return None

        return self._query(sql_str, params=params)

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
              from {symbol}{table_name}{symbol}
             where 1 = 1
                   {condition_sql}
        """.format(
            symbol=self.field_symbol,
            table_name=self.table_name,
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
                    new_conditions.append({SQL_QUERY_FIELD: query_name, SQL_QUERY_OPERATE: operate, SQL_QUERY_VALUE: item})
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
            fields_sql_list =[]
            for f in fields:
                field_str = self.field_symbol + f + self.field_symbol
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

    def _query(self, sql_str, params=None):
        rows = self.__execute(sql_str, params)
        return rows

    def paginate_query(self, condition, page_index=1, page_size=20, fields=None, order_by=None):
        sql_str, params = self._generate_query_sql(condition, fields=fields, order_by=order_by)
        if not sql_str:
            self.exec_state.failure('生成SQL失败')
            return None

        return self._paginate_query(sql_str, params=params, page_index=page_index, page_size=page_size)

    def _paginate_query(self, sql_str, params=None, page_index=1, page_size=20):
        query_row_count_sql = "select count(1) row_count from (%s) t" % sql_str
        rows = self.__execute(query_row_count_sql, params)
        row_count = 0

        if row_count <= (page_index - 1) * page_size:
            page_index = 1

        offset = (page_index - 1) * page_size
        limit = page_size
        query_sql = "select * from (%s) t limit %s offset %s" % (sql_str, limit, offset)
        result = self.__execute(query_sql, params)

        return result

    def __execute(self, sql_str, params=None, fetch_type=None):
        try:
            self.cur.execute(sql_str, params)
            rows = self.cur.fetchall()
        except PgError as e:
            self.exec_state.failure("DB执行SQL失败'{0}'".format(str(e)))
            return None
        except Exception as e:
            self.exec_state.failure("执行SQL失败'{0}'".format(str(e)))
            return None

        return rows

    def delete(self):
        return None

    def batch_create(self):
        return None

    def update(self):
        return None

    def _write(self):
        return None

    # def _generate_insert_sql(self, field_default_value_dict={}):
    #     parameter_list = []
    #     insert_sql = 'Insert Into %s%s%s (%s' % (self.__join_char, self._table_name, self.__join_char, self.__join_char)
    #     insert_sql_name = []
    #     insert_sql_paras = []
    #
    #     if Global.SAVE_FLAG_NAME in field_default_value_dict.keys():
    #         field_default_value_dict.pop(Global.SAVE_FLAG_NAME)
    #
    #     if self.__exists_log_field:
    #         field_default_value_dict.update({'write_date': datetime.datetime.utcnow()})
    #         field_default_value_dict.update({'write_uid': self.user_id})
    #         field_default_value_dict.update({'create_date': datetime.datetime.utcnow()})
    #         field_default_value_dict.update({'create_uid': self.user_id})
    #
    #     if self.__odoo_table and self._psqlOperate.db_type == DBTypeEnum.PostgreDB.value[0]:
    #         insert_sql_name.append(self._primary_key_list[0])
    #         insert_sql_paras.append("nextval('%s_id_seq')" % self._table_name)
    #
    #     for key in field_default_value_dict.keys():
    #         insert_sql_name.append(key)
    #         insert_sql_paras.append('%s')
    #
    #         field_value = field_default_value_dict[key]
    #         if isinstance(field_value, dict):
    #             field_value = json.dumps(field_value)
    #
    #         parameter_list.append(field_value)
    #
    #     if not insert_sql_name:
    #         return False, False
    #
    #     insert_sql_name = str.join('%s,%s' % (self.__join_char, self.__join_char), insert_sql_name)
    #     insert_sql = insert_sql + insert_sql_name + '%s) values (' % self.__join_char + str.join(',', insert_sql_paras) + ')'
    #
    #     if self._primary_key_list and self._psqlOperate.db_type == DBTypeEnum.PostgreDB.value[0]:
    #         return_sql = ' returning "%s"' % str.join('","', self._primary_key_list)
    #
    #         insert_sql += return_sql
    #
    #     return insert_sql, parameter_list
    #
    # def __add_extra_value(self, field_value_dict):
    #     field_value_dict.pop(Global.SAVE_FLAG_NAME, None)
    #
    #     if self.__exists_log_field:
    #         field_value_dict.update({
    #             'write_date': datetime.datetime.utcnow(),
    #             'write_uid': self.user_id,
    #             'create_date': datetime.datetime.utcnow(),
    #             'create_uid': self.user_id,
    #         })
    #
    #     return field_value_dict
    #
    # def _generate_batch_insert_sql(self, values_iter):
    #     insert_sql = 'Insert Into %s%s%s (' % (self.__join_char, self._table_name, self.__join_char,)
    #
    #     value_list = [self.__add_extra_value(item) for item in values_iter]
    #     insert_sql_name_list = list(value_list[0].keys())
    #
    #     parameter_list = []
    #     for value_dict in value_list:
    #         values_tuple = tuple(value_dict.get(key) for key in insert_sql_name_list)
    #
    #         values_tuple = tuple(json.dumps(value) if isinstance(value, dict) else value for value in values_tuple)
    #
    #         parameter_list.append(values_tuple)
    #
    #     template = ','.join(['%s'] * len(insert_sql_name_list))
    #     if self.__odoo_table and self._psqlOperate.db_type == DBTypeEnum.PostgreDB.value[0]:
    #         insert_sql_name_list.insert(0, self._primary_key_list[0])
    #         if self._table_name == 'theoretical_final_freight':
    #             template = "nextval('%s_seq'), " % self._table_name + template
    #         else:
    #             template = "nextval('%s_id_seq'), " % self._table_name + template
    #
    #
    #     template = '(' + template + ')'
    #     insert_sql_name = ",".join("%s%s%s" % (self.__join_char, name, self.__join_char,) for name in insert_sql_name_list)
    #     insert_sql = insert_sql + insert_sql_name + ') values'
    #
    #     if self._psqlOperate.db_type == DBTypeEnum.PostgreDB.value[0]:
    #         insert_sql += ' %s '
    #
    #     return insert_sql, parameter_list, template
    #
    # def _generate_update_sql(self, field_default_value_dict={}, update_key_list=None):
    #     #v1.0 update_key_list only support str list
    #     #v2.0 update_key_list support either str list or tuple list
    #     if not update_key_list:
    #         update_key_list = []
    #     elif isinstance(update_key_list, str):
    #         update_key_list = [update_key_list]
    #     elif isinstance(update_key_list, tuple):
    #         update_key_list = [update_key_list]
    #
    #     # True: use key list generate sql condition
    #     # False: use tuple list generate sql condition
    #     condition_by_key = True
    #     if update_key_list:
    #         key_count, tuple_count = 0, 0
    #         for item in update_key_list:
    #             if isinstance(item, tuple):
    #                 tuple_count += 1
    #             elif isinstance(item, str):
    #                 key_count += 1
    #             else:
    #                 self.error_message = "update key type not support."
    #                 return False, False
    #
    #         if key_count > 0 and tuple_count > 0:
    #             self.error_message = "update key type support either str or tuple."
    #             return False, False
    #         elif tuple_count > 0:
    #             condition_by_key = False
    #
    #     self.__update_key_list = update_key_list
    #     if not self.__update_key_list:
    #         self.__update_key_list.extend(self._primary_key_list)
    #
    #     if Global.SAVE_FLAG_NAME in field_default_value_dict.keys():
    #         field_default_value_dict.pop(Global.SAVE_FLAG_NAME)
    #
    #     if self.__exists_log_field:
    #         field_default_value_dict.update({'write_date': datetime.datetime.utcnow()})
    #         field_default_value_dict.update({'write_uid': self.user_id})
    #
    #     set_sql_list = []
    #     parameter_list = []
    #     sql_condition = []
    #     for key in field_default_value_dict.keys():
    #         field_value = field_default_value_dict[key]
    #         if isinstance(field_value, dict):
    #             field_value = json.dumps(field_value)
    #
    #         if condition_by_key and key in self.__update_key_list:
    #             sql_condition.extend(SQC.qc((key, "=", field_value)))
    #             continue
    #
    #         set_sql = ' %s%s%s = %%s ' % (self.__join_char, key, self.__join_char)
    #         set_sql_list.append(set_sql)
    #         parameter_list.append(field_value)
    #
    #     if not condition_by_key and self.__update_key_list:
    #         sql_condition.extend(SQC.qc(self.__update_key_list))
    #
    #     where_sql, where_sql_parameter_list = self._get_sub_sql_conditon_and_paras(sql_condition)
    #
    #     if not set_sql_list:
    #         self.error_message = "no set item value"
    #         return False, False
    #
    #     if not where_sql:
    #         self.error_message = "need set update condition"
    #         return False, False
    #
    #     parameter_list.extend(where_sql_parameter_list)
    #
    #     set_sql = str.join(',', set_sql_list)
    #     update_sql = 'update %s%s%s set %s where 1 = 1 %s' % (self.__join_char, self._table_name, self.__join_char,
    #                                                           set_sql, where_sql)
    #
    #     return update_sql, parameter_list
    #
    # def _generate_batch_update_sql(self, update_data_list, update_key_list=None, field_type=None):
    #     if not update_key_list:
    #         update_key_list = []
    #     elif isinstance(update_key_list, str):
    #         update_key_list = [update_key_list]
    #
    #     if not field_type:
    #         field_type = {}
    #
    #     condition_by_key = True
    #
    #     self.__update_key_list = update_key_list
    #     if not self.__update_key_list:
    #         self.__update_key_list.extend(self._primary_key_list)
    #
    #     for update_data in update_data_list:
    #         update_data.pop(Global.SAVE_FLAG_NAME, None)
    #         if self.__exists_log_field:
    #             update_data.update({'write_date': datetime.datetime.utcnow()})
    #             update_data.update({'write_uid': self.user_id})
    #
    #     set_sql_list = []
    #     sql_condition = []
    #
    #     key_list = list(update_data_list[0].keys())
    #     for key in key_list:
    #         if condition_by_key and key in self.__update_key_list:
    #             where_sub_sql = ' %s.%s%s%s = dt.%s%s%s ' % (self._table_name, self.__join_char, key, self.__join_char, self.__join_char, key, self.__join_char)
    #             sql_condition.append(where_sub_sql)
    #         else:
    #             set_sql = ' %s%s%s = dt.%s%s%s ' % (self.__join_char, key, self.__join_char, self.__join_char, key, self.__join_char)
    #             set_sql_list.append(set_sql)
    #
    #     if not set_sql_list:
    #         self.error_message = "no set item value"
    #         return False, False, False
    #
    #     if not sql_condition:
    #         self.error_message = "need set update condition"
    #         return False, False, False
    #
    #     where_sql = str.join(' And ', sql_condition)
    #     key_sql = str.join(',', key_list)
    #     set_sql = str.join(',', set_sql_list)
    #     update_sql = 'update %s%s%s set %s  from (values %%s) as dt (%s) where 1 = 1 and %s' % (self.__join_char, self._table_name,
    #                                                                          self.__join_char, set_sql, key_sql, where_sql)
    #
    #     data_list = [
    #         tuple(update_data.get(key) if not isinstance(update_data.get(key), dict) else json.dumps(update_data.get(key))for key in key_list)
    #         for update_data in update_data_list
    #     ]
    #
    #     type_dict = {f: data_type for data_type in field_type for f in (field_type.get(data_type) or []) if data_type in SQL_TYPE_MAP.keys()}
    #     template_keys = ("::" + SQL_TYPE_MAP.get(type_dict.get(key)) if type_dict.get(key) else "" for key in key_list)
    #     template =  '(' + ','.join("%s" + key for key in template_keys) + ')'
    #
    #     return update_sql, data_list, template
    #
    #
    #
    # def _generate_group_by_select_sql(self, src_select_sql, group_by, query_name_list=[], show_name_list=None):
    #     if not show_name_list:
    #         show_name_list = query_name_list
    #
    #     group_by = self.__deal_multi_column_group_by(group_by)
    #
    #     group_name_list = [item for item in group_by]
    #     need_group_name_list = [item for item in group_by if item.get("is_group")]
    #
    #     group_by_str = ""
    #     new_query_name_list, new_show_name_list = [], []
    #     if not need_group_name_list:
    #         for query_name in query_name_list:
    #             if query_name in group_name_list:
    #                 continue
    #
    #             old_group_name_list, new_group_name_list, show_names_list = self.__get_new_group_name([query_name],
    #                                                                                                   query_name_list,
    #                                                                                                   show_name_list)
    #
    #             for old_group_name in old_group_name_list:
    #                 new_query_name_list.append(old_group_name)
    #                 new_show_name_list.append(show_names_list[old_group_name_list.index(old_group_name)])
    #     else:
    #         group_name_list = [need_group_name.get("group_name") for need_group_name in need_group_name_list]
    #
    #         old_group_name_list, new_group_name_list, show_names_list = self.__get_new_group_name(group_name_list,
    #                                                                                               query_name_list,
    #                                                                                               show_name_list)
    #         for new_group_name in new_group_name_list:
    #             new_query_name_list.append(new_group_name)
    #             new_show_name_list.append(show_names_list[new_group_name_list.index(new_group_name)])
    #
    #         new_query_name_list.append("count(1)")
    #         new_show_name_list.append("cnt")
    #
    #         group_by_str = " Group by %s" % str.join(",", new_group_name_list)
    #
    #         for need_group_name in need_group_name_list:
    #             for item in need_group_name.get("aggregate_column",[]):
    #                 new_query_name_list.append('%s' % (item.get("aggregate_function")))
    #                 new_show_name_list.append(item.get("name"))
    #
    #     sql_query_name_list = []
    #     for index in range(len(new_query_name_list)):
    #         sql_query_name_list.append('%s %s%s%s' % (new_query_name_list[index], self.__join_char,
    #                                                   new_show_name_list[index], self.__join_char))
    #
    #     select_sql = """
    #                 select %s
    #                   from (%s) t
    #                  where 1 = 1
    #                   %s
    #                    """ % (str.join(',', sql_query_name_list), src_select_sql, group_by_str)
    #
    #     return select_sql
    #
    # def __get_new_group_name(self, group_name_list, query_name_list, show_name_list):
    #     old_group_name_list, new_group_name_list, show_names_list = [], [], []
    #
    #     for group_name in group_name_list:
    #         if ":" in group_name:
    #             split_array = group_name.split(':')
    #             old_group_name = split_array[0]
    #             date_part = split_array[1]
    #             date_type = split_array[2] if len(split_array) == 3 else 'date'
    #
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
    #
    #
    #             show_name = "%s:%s" % (show_name_list[query_name_list.index(old_group_name)], date_part)
    #         else:
    #             old_group_name = group_name
    #             new_group_name = group_name
    #             show_name = show_name_list[query_name_list.index(old_group_name)]
    #
    #         old_group_name_list.append(old_group_name)
    #         new_group_name_list.append(new_group_name)
    #         show_names_list.append(show_name)
    #
    #     return old_group_name_list, new_group_name_list, show_names_list
    #
    # def __deal_multi_column_group_by(self, group_by):
    #     new_group_by = []
    #     for group_by_item in group_by:
    #         group_name = group_by_item.get("group_name")
    #         is_group = group_by_item.get("is_group")
    #         if not is_group:
    #             new_group_by.append(group_by_item)
    #             continue
    #
    #         if "," not in group_name:
    #             new_group_by.append(group_by_item)
    #             continue
    #
    #         multi_columns = group_name.split(",")
    #         for group_column in multi_columns:
    #             exists_group_by = [item for item in group_by if item.get("group_name") == group_column.strip()]
    #             if exists_group_by:
    #                 exists_group_by[0].update({"is_group": True})
    #             else:
    #                 new_item = group_by_item.copy()
    #                 new_item.update({"group_name": group_column.strip()})
    #
    #                 if multi_columns.index(group_column) != 0:
    #                     new_item.update({"aggregate_column": []})
    #
    #                 new_group_by.append(new_item)
    #
    #     return new_group_by
    #
    #

    #

    #
    # def _get_sub_sql_conditon_and_paras(self, sql_condition):
    #     where_sql_list = []
    #     where_sql_parameter_list = []
    #     for item in sql_condition:
    #         if item.get(Global.SQL_QUERY_OPERATE) in (Global.SQL_NULL, Global.SQL_NOTNULL):
    #             where_sql_list.append('And %s%s%s is %s ' % (
    #             self.__join_char, item.get(Global.SQL_QUERY_FIELD), self.__join_char,
    #             item.get(Global.SQL_QUERY_OPERATE)))
    #         else:
    #             where_sql_list.append('And %s%s%s %s %%s ' % (self.__join_char, item.get(Global.SQL_QUERY_FIELD), self.__join_char,
    #                                                           item.get(Global.SQL_QUERY_OPERATE)))
    #             where_sql_parameter_list.append(item.get(Global.SQL_QUERY_VALUE))
    #
    #     if not where_sql_list:
    #         return False, False
    #
    #     where_sql = str.join(' ', where_sql_list)
    #
    #     return where_sql, where_sql_parameter_list
    #
    # def create(self, insert_dict={}):
    #     need_save_dict = {}
    #     for key in insert_dict.keys():
    #         if key == "user_browser_tz":
    #             continue
    #
    #         need_save_dict.update({key: insert_dict[key]})
    #
    #     for key2 in self._add_initial_data.keys():
    #         if key2 in insert_dict.keys():
    #             continue
    #
    #         need_save_dict.update({key2: self._add_initial_data[key2]})
    #
    #     insert_sql, parameter_list = self._generate_insert_sql(need_save_dict)
    #
    #     if not insert_sql:
    #         self.error_code = Global.response_error_code
    #         self.error_message = 'generate insert sql error'
    #         return False
    #
    #     result = self._create(insert_sql, paras=parameter_list)
    #     if self.error_code == Global.response_error_code:
    #         return result
    #
    #     if self._psqlOperate.db_type == DBTypeEnum.MySQLDB.value[0]:
    #         return_sql = 'SELECT LAST_INSERT_ID() as last_id'
    #         result = self._query(return_sql)
    #         if self.error_code == Global.response_error_code:
    #             return result
    #
    #         if self.__result_is_dict:
    #             result = result[0].get("last_id")
    #         else:
    #             result = result[0].last_id
    #
    #     return result
    #
    # def __initial_add_data(self, value_data):
    #     value_data.pop("user_browser_tz", None)
    #     value_data.update({key: value for key, value in self._add_initial_data.items() if key not in value_data.keys()})
    #     return value_data
    #
    # def batch_create(self, insert_value_list=[], page_size=1000, fetch=False):
    #     if not insert_value_list:
    #         return True
    #
    #     data_keys = insert_value_list[0].keys()
    #     if not data_keys:
    #         self.error_code = Global.response_error_code
    #         self.error_message = 'insert value is empty'
    #         return False
    #
    #     if any(value_dict.keys() != data_keys for value_dict in insert_value_list):
    #         self.error_code = Global.response_error_code
    #         self.error_message = 'insert value key is not same'
    #         return False
    #
    #     value_iter = (self.__initial_add_data(value_data) for value_data in insert_value_list)
    #
    #     insert_sql, parameter_list, template = self._generate_batch_insert_sql(value_iter)
    #
    #     if not insert_sql:
    #         self.error_code = Global.response_error_code
    #         self.error_message = 'generate insert sql error'
    #         return False
    #
    #     result = self._batch_create(insert_sql, paras=parameter_list, template=template, page_size=page_size,
    #                                 fetch=fetch)
    #     if self.error_code == Global.response_error_code:
    #         return result
    #
    #     return result
    #
    #
    # def batch_create_odoo(self, insert_value_list=[], page_size=1000, fetch=False):
    #     """
    #     兼容odoo数据表的创建
    #     :param insert_value_list:
    #     :param page_size:
    #     :param fetch:
    #     :return:
    #     """
    #     self.__odoo_table = True
    #
    #     result = self.batch_create(insert_value_list, page_size=page_size, fetch=fetch)
    #
    #     self.__odoo_table = False
    #
    #     if self.error_code == Global.response_error_code:
    #         return False
    #
    #     return result
    #
    # def create_odoo(self, insert_dict={}):
    #     """
    #     兼容odoo数据表的创建
    #     :param insert_dict:
    #     :return:
    #     """
    #     self.__odoo_table = True
    #
    #     result = self.create(insert_dict)
    #
    #     self.__odoo_table = False
    #
    #     if self.error_code == Global.response_error_code:
    #         return False
    #
    #     if self._primary_key_list and self._psqlOperate.db_type == DBTypeEnum.PostgreDB.value[0]:
    #         return result.get(self._primary_key_list[0])
    #     else:
    #         return result
    #
    # def create_no_log(self, insert_dict={}):
    #     """
    #     兼容数据表的没有create_uid, create_date, write_uid, write_date等日志字段表的创建
    #     :param insert_dict:
    #     :return:
    #     """
    #     self.__exists_log_field = False
    #
    #     result = self.create(insert_dict)
    #
    #     self.__exists_log_field = True
    #
    #     if self.error_code == Global.response_error_code:
    #         return False
    #
    #     if self._primary_key_list and self._psqlOperate.db_type == DBTypeEnum.PostgreDB.value[0]:
    #         return result.get(self._primary_key_list[0])
    #     else:
    #         return result
    #
    # def create_odoo_no_log(self, insert_dict={}):
    #     """
    #     兼容odoo数据表并且没有create_uid, create_date, write_uid, write_date等日志字段表的创建
    #     :param insert_dict:
    #     :return:
    #     """
    #     self.__odoo_table = True
    #     self.__exists_log_field = False
    #
    #     result = self.create(insert_dict)
    #
    #     self.__odoo_table = True
    #     self.__exists_log_field = False
    #
    #     if self.error_code == Global.response_error_code:
    #         return False
    #
    #     if self._primary_key_list and self._psqlOperate.db_type == DBTypeEnum.PostgreDB.value[0]:
    #         return result.get(self._primary_key_list[0])
    #     else:
    #         return result
    #
    #
    # def _batch_create(self, insert_sql, paras=[], template=None, page_size=1000, fetch=True):
    #     paras = paras if not paras else tuple(paras)
    #
    #     result = self._psqlOperate.execute_batch_create_scalar(insert_sql, parameters=paras, template=template, page_size=page_size, fetch=fetch)
    #     if self._psqlOperate.exists_error:
    #         self.error_code = Global.response_error_code
    #         self.error_message = self._psqlOperate.error_message
    #         return False
    #
    #     if not result:
    #         self.error_code = Global.response_error_code
    #         self.error_message = 'no data add'
    #         return False
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None
    #
    #     return result
    #
    # def _create(self, insert_sql, paras=None):
    #     paras = paras if not paras else tuple(paras)
    #
    #     result = self._psqlOperate.execute_create_scalar(insert_sql, parameters=paras)
    #     if self._psqlOperate.exists_error:
    #         self.error_code = Global.response_error_code
    #         self.error_message = self._psqlOperate.error_message
    #         return False
    #
    #     if not result:
    #         self.error_code = Global.response_error_code
    #         self.error_message = 'no data add'
    #         return False
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None
    #
    #     return result
    #
    # def query_pagination(self, query_condition, page_index=1, page_size=80, query_name_list=None, show_name_list=None,
    #                      order_by=None, group_by=None):
    #     if not query_name_list:
    #         query_name_list = []
    #
    #     if not show_name_list:
    #         show_name_list = []
    #
    #     sql_text, parameter_list = self._generate_query_sql(query_condition, query_name_list=query_name_list,
    #                                                         show_name_list=show_name_list, order_by=order_by,
    #                                                         group_by=group_by)
    #     if not sql_text:
    #         self.error_code = Global.response_error_code
    #         self.error_message = 'generate select sql script error'
    #         return None, None, None
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None
    #
    #     return self._query_pagination(sql_text, paras=parameter_list, page_index=page_index, page_size=page_size)
    #
    # def _query_pagination(self, sql_text, paras=None, page_index=1, page_size=80):
    #     query_row_count_sql = "select count(1) from (%s) t" % sql_text
    #
    #     row_count = self._psqlOperate.execute_scalar(query_row_count_sql, parameters=paras)
    #     if self._psqlOperate.exists_error:
    #         self.error_code = Global.response_error_code
    #         self.error_message = self._psqlOperate.error_message
    #         return None, None, None
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None
    #
    #     if row_count == 0:
    #         return 0, [], 1
    #
    #     if row_count <= (page_index - 1) * page_size:
    #         page_index = 1
    #
    #     offset = (page_index - 1) * page_size
    #     limit = page_size
    #     query_sql = "select * from (%s) t limit %s offset %s" % (sql_text, limit, offset)
    #     result = self._psqlOperate.execute_return_model_list(query_sql, parameters=paras)
    #     if self._psqlOperate.exists_error:
    #         self.error_code = Global.response_error_code
    #         self.error_message = self._psqlOperate.error_message
    #         return None, None, None
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None
    #
    #     obj_list = self.__convert_query_data_2_return_data(result)
    #
    #     return row_count, obj_list, page_index
    #
    # def query(self, query_condition, query_name_list=None, show_name_list=None, offset=None, limit=None, order_by=None,
    #           count=False, group_by=None, distinct_search=False):
    #     warnings.warn("query is deprecated, use search function", DeprecationWarning)
    #
    #     if not query_name_list:
    #         query_name_list = []
    #
    #     if not show_name_list:
    #         show_name_list = []
    #
    #     sql_text, parameter_list = self._generate_query_sql(query_condition, query_name_list=query_name_list,
    #                                                         show_name_list=show_name_list, offset=offset, limit=limit,
    #                                                         order_by=order_by, count=count, group_by=group_by,
    #                                                         distinct_search=distinct_search)
    #     if not sql_text:
    #         return None
    #
    #     return self._query(sql_text, paras=parameter_list)
    #
    # def _query(self, select_sql, paras=None):
    #     result = self._psqlOperate.execute_return_model_list(select_sql, parameters=paras)
    #     if self._psqlOperate.exists_error:
    #         self.error_code = Global.response_error_code
    #         self.error_message = self._psqlOperate.error_message
    #         return False
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None
    #
    #     obj_list = self.__convert_query_data_2_return_data(result)
    #
    #     return obj_list
    #
    # def __convert_query_data_2_return_data(self, result):
    #     obj_list = []
    #     result_is_dict = False
    #     if isinstance(self._psqlOperate, MysqlOperate):
    #         result_is_dict = True
    #
    #     if self.__result_is_dict:
    #         if result_is_dict:
    #             obj_list = result
    #         else:
    #             obj_list = [item.convert_to_json() for item in result]
    #     else:
    #         if result_is_dict:
    #             obj_list = self._psqlOperate.json_to_base_model(result)
    #         else:
    #             obj_list = result
    #
    #     return obj_list
    #
    # def write(self, update_dict={}, update_key_list=None):
    #     """
    #     :param update_dict:
    #     :param update_key_list：指定更新键条件
    #     :return:
    #     """
    #     need_update_dict = {}
    #     for key in update_dict.keys():
    #         if key == "user_browser_tz":
    #             continue
    #
    #         need_update_dict.update({key: update_dict[key]})
    #
    #     update_sql, parameter_list = self._generate_update_sql(need_update_dict, update_key_list=update_key_list)
    #     if not update_sql:
    #         self.error_code = Global.response_error_code
    #
    #         if not self.error_message:
    #             self.error_message = 'generate update sql error'
    #
    #         return False
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None
    #
    #     return self._write(update_sql, paras=parameter_list)
    #
    # def _write(self, update_sql, paras=None):
    #     result = self._psqlOperate.execute_update_scalar(update_sql, parameters=paras)
    #     if self._psqlOperate.exists_error:
    #         self.error_code = Global.response_error_code
    #         self.error_message = self._psqlOperate.error_message
    #         return False
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None
    #
    #     if not result:
    #         self.error_code = Global.no_data_affect
    #         self.error_message = 'no data update'
    #         return False
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None
    #
    #     return True
    #
    # def batch_write(self, update_data_list=[], update_key_list=None, page_size=1000, fetch=False, field_type=None):
    #     """
    #     :param update_data_list:
    #     :param update_key_list：指定更新数据的条件key
    #     :param page_size：每次执行数量
    #     :param fetch：是否抓取返回值
    #     :param field_type：指定每个键的数据类型, 针对部分情况下, 存在所有数值为None值时使用,支持 浮点数,整数,bool值, 时间,日期, JSON
    #     如果数据中有JSON, 那么必须指定字段类型, 字符类型无需指定,指定也无效
    #     {
    #         "int":["int_field"],
    #         "float": ["float_field"],
    #         "bool":["bool_field"],
    #         "datetime":["datetime_field"],
    #         "date":["datetime_field"],
    #         "json":["json_field"],
    #     }
    #     :return:
    #     """
    #     if not update_data_list:
    #         return True
    #
    #     data_keys = update_data_list[0].keys()
    #
    #     for update_dict in update_data_list:
    #         update_dict.pop("user_browser_tz", None)
    #         if data_keys != update_dict.keys():
    #             self.error_code = Global.response_error_code
    #             self.error_message = 'insert value key is not same'
    #             return False
    #
    #     update_sql, parameter_list, template = self._generate_batch_update_sql(update_data_list, update_key_list=update_key_list, field_type=field_type)
    #     if not update_sql:
    #         self.error_code = Global.response_error_code
    #
    #         if not self.error_message:
    #             self.error_message = 'generate update sql error'
    #
    #         return False
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None
    #
    #     return self._batch_write(update_sql, paras=parameter_list, template=template, page_size=page_size, fetch=fetch)
    #
    # def _batch_write(self, update_sql, paras=None, template=None, page_size=1000, fetch=True):
    #     result = self._psqlOperate.execute_batch_update_scalar(update_sql, parameters=paras, template=template, page_size=page_size, fetch=fetch)
    #     if self._psqlOperate.exists_error:
    #         self.error_code = Global.response_error_code
    #         self.error_message = self._psqlOperate.error_message
    #         return False
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None
    #
    #     if not result:
    #         self.error_code = Global.no_data_affect
    #         self.error_message = 'no data update'
    #         return False
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None
    #
    #     return True
    #
    # def delete(self, delete_condition={}):
    #     # v1.0 update_key_list only support dict
    #     # v2.0 update_key_list support either dict or (tuple or tuple list)
    #     if not delete_condition:
    #         delete_condition = []
    #     elif isinstance(delete_condition, tuple):
    #         delete_condition = [delete_condition]
    #
    #     # True: use key list generate sql condition
    #     # False: use tuple list generate sql condition
    #     condition_by_key = True
    #     if delete_condition:
    #         key_count, tuple_count = 0, 0
    #         for item in delete_condition:
    #             if isinstance(item, tuple):
    #                 tuple_count += 1
    #             elif isinstance(item, str):
    #                 key_count += 1
    #             else:
    #                 self.error_code = Global.response_error_code
    #                 self.error_message = "update key type not support."
    #                 return False
    #
    #         if key_count > 0 and tuple_count > 0:
    #             self.error_code = Global.response_error_code
    #             self.error_message = "update key type support either str or tuple."
    #             return False
    #         elif tuple_count > 0:
    #             condition_by_key = False
    #
    #     delete_sql = "delete from %s where 1= 1 " % self._table_name
    #
    #     sql_condition = []
    #     if condition_by_key and delete_condition:
    #         for key in delete_condition:
    #             sql_condition.extend(SQC.qc((key, "=", delete_condition[key])))
    #     elif not condition_by_key and delete_condition:
    #         sql_condition.extend(SQC.qc(delete_condition))
    #
    #     where_sql, parameter_list = self._get_sub_sql_conditon_and_paras(sql_condition)
    #
    #     if not where_sql:
    #         self.error_code = Global.response_error_code
    #         self.error_message = "generate delete sql error."
    #         return False
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None
    #
    #     delete_sql += where_sql
    #
    #     return self._delete(delete_sql, paras=parameter_list)
    #
    # def _delete(self, delete_sql, paras=None):
    #     result = self._psqlOperate.execute_update_scalar(delete_sql, paras)
    #     if self._psqlOperate.exists_error:
    #         self.error_code = Global.response_error_code
    #         self.error_message = self._psqlOperate.error_message
    #         return False
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None
    #
    #     if not result:
    #         self.error_code = Global.no_data_affect
    #         self.error_message = 'no data delete'
    #         return False
    #     else:
    #         self.error_code = Global.response_correct_code
    #         self.error_message = None
    #
    #     return True
    #
    # def search(self, domain, query_name_list=None, show_name_list=None, offset=None, limit=None, order_by=None,
    #           count=False, group_by=None, distinct_search=False):
    #     query_condition = SQC.qc(domain)
    #     if isinstance(query_condition, type(None)):
    #         self.error_code = Global.response_error_code
    #         self.error_message = "domain type error[tuple or list]."
    #         return []
    #
    #     return self.query(query_condition, query_name_list=query_name_list, show_name_list=show_name_list,
    #                       offset=offset, limit=limit, order_by=order_by, count=count, group_by=group_by,
    #                       distinct_search=distinct_search)


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

    def set_state(self):
        self.state = DBResultState.SUCCESS.value
        self.error_msg = ""