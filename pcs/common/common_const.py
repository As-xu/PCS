__all__ = ['QOP', 'JCK', 'SQL_TYPE_MAP']

class JsonCommonKey:
    PAGE_INDEX = "page_index"
    PAGE_limit = "page_limit"
    MODIFY_TYPE = 'modify_type'
    QUERY_CONDITION = 'query_params'
    ORDER_BY = "order"
    GROUP_BY = "group"


class QueryOperator:
    EQ = '='
    NEQ = '!='
    GE = '>='
    GT = '>'
    LE = '<='
    LT = '<'
    OR = '|'
    NULL = 'null'
    NOTNULL = 'not null'
    LIKE = 'like'
    ILIKE = 'ilike'
    NOT_LIKE = 'not like'
    NOT_ILIKE = 'not ilike'
    L_LIKE = 'l_like'
    R_LIKE = 'r_like'
    L_ILIKE = 'l_ilike'
    R_ILIKE = 'r_ilike'
    IN = 'in'
    NOT_IN = 'not in'
    RE = 're'
    NOT_RE = 'not re'
    # 暂不考虑
    # EXIST = 'exists'
    # NOT_EXIST = 'not exists'

    @classmethod
    def get_query_ops(cls):
        return tuple(v for k, v in QueryOperator.__dict__.items() if k.isupper())

    @classmethod
    def have_op(cls, op):
        return any(v==op for k, v in QueryOperator.__dict__.items() if k.isupper())

SQL_TYPE_MAP = {
    "int": "INTEGER", "float": "NUMERIC", "bool": "BOOLEAN", "datetime": "TIMESTAMP", "date": "DATE", "json": "JSON",
}

QOP = QueryOperator
JCK = JsonCommonKey