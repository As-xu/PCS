
SQL_QUERY_FIELD = 'field'
SQL_QUERY_OPERATE = 'operate'
SQL_OR = '|'
SQL_NULL = 'null'
SQL_NOTNULL = 'not null'
SQL_QUERY_OPERATE_VALUES = [
    '>', '=', '<', '>=', '<=', '!=', 'prefix_like', 'llike', 'like', 'rlike', 'not like',
    'suffix_like', 'ilike', 'not ilike', SQL_NULL, SQL_NOTNULL, 'in', 'not in', 'regular_exp', 'not regular_exp',
    SQL_OR, 'in_or_like', 'in_or_rlike', 'in_or_llike',
    'in_or_prefix_like', 'in_or_suffix_like', 'in_or_=', "!~", "~"
]
SQL_QUERY_VALUE = 'value'
PAGE_INDEX = "page_index"
PAGE_SIZE = "page_size"
QUERY_CONDITION = 'query_condition'
ORDER_BY = "order_by"
GROUP_BY = "group_by"