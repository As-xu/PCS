import logging
import redis
import socket
from datetime import datetime
_logger = logging.getLogger(__name__)


class RedisOperate(object):
    def __init__(self, cli, db=0):
        self.cli = cli
        self.db = db
        if self.db != 0:
            success, error_info = self.select_db(self.db)
            if not success:
                raise Exception(error_info)
    # def set_value(self, key, value, time=None):
    #     try:
    #         if time:
    #             res = self.cli.setex(key, value, time)
    #         else:
    #             res = self.cli.set(key, value)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res
    #
    # def batch_set_value(self, map_dict):
    #     try:
    #         res = self.cli.mset(map_dict)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res
    #
    # def get_value(self, key):
    #     try:
    #         res = self.cli.get(key).decode()
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res
    #
    # def batch_get_value(self, keys):
    #     try:
    #         res = self.cli.mget(keys).decode()
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res

    def set_hash(self, name, key, value):
        try:
            res = self.cli.hset(name, key, value)
        except Exception as e:
            return False, str(e)

        return True, res

    def batch_set_hash(self, name, map_dict):
        try:
            res = self.cli.hset(name, mapping=map_dict)
        except Exception as e:
            return False, str(e)

        return True, res

    def get_hash(self, name, key=None):
        try:
            if key:
                res = self.cli.hget(name, key)
            else:
                res = self.cli.hgetall(name)
        except Exception as e:
            return False, str(e)

        return True, res

    # def batch_get_hash(self, name, keys):
    #     try:
    #         res = self.cli.hmget(name, keys)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res

    def exists_hash(self, name, key):
        try:
            res = self.cli.hexists(name, key)
        except Exception as e:
            return False, str(e)

        return True, res

    # def get_hash_keys(self, name):
    #     try:
    #         res = self.cli.hkeys(name)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res
    #
    # def del_hash(self, name, keys=None):
    #     try:
    #         if keys:
    #             res = self.cli.hdel(name, keys)
    #         else:
    #             res = self.cli.delete(name)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res

    # def left_push_list(self, name, values):
    #     try:
    #         res = self.cli.lpush(name, values)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res
    #
    # def len_list(self, name):
    #     try:
    #         res = self.cli.llen(name)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res
    #
    # def insert_list(self, name, ref_value, value, before=True):
    #     try:
    #         if before:
    #             where = "BEFORE"
    #         else:
    #             where = "AFTER"
    #         res = self.cli.linsert(name, where, ref_value, value)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res
    #
    # def set_index_list(self, name, index, value):
    #     try:
    #         if self.cli.llen(name) < index - 1:
    #             return False, "索引错误, 大于列表长度"
    #         res = self.cli.lset(name, index, value)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res
    #
    # def get_index_list(self, name, index):
    #     try:
    #         if self.cli.llen(name) < index - 1:
    #             return False, "索引错误, 大于列表长度"
    #
    #         res = self.cli.lindex(name, index)
    #
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res
    #
    # def get_range_list(self, name, start, end):
    #     try:
    #         res = self.cli.lrange(name, start, end)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res
    #
    # def del_list(self, name, value, num):
    #     try:
    #         res = self.cli.lrem(name, value, num)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res

    def add_set(self, name, values):
        if not values:
            return True, True

        try:
            res = self.cli.sadd(name, *values)
        except Exception as e:
            return False, str(e)

        return True, res

    # def len_set(self, name):
    #     try:
    #         res = self.cli.scard(name)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res
    #
    # def exists_set(self, name, value):
    #     try:
    #         res = self.cli.sismember(name, value)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res

    def get_set(self, name, num=None):
        try:
            if num:
                res = self.cli.srandmember(name, num)
            else:
                res = self.cli.smembers(name)
        except Exception as e:
            return False, str(e)

        return True, res

    # def pop_set(self, name):
    #     try:
    #         res = self.cli.spop(name)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res
    #
    # def del_set(self, name, values):
    #     try:
    #         res = self.cli.srem(name, values)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res

    def delete_name(self, names):
        try:
            # for name in names:
            #     if name == 'general_code':
            #         import inspect
            #         frame_list = inspect.getouterframes(inspect.currentframe(), 3)
            #         log_content = "***********************************\n"
            #         for frame in frame_list:
            #             if 'woltu_addons' in frame.filename:
            #                 log_content += frame.filename + "\n"
            #                 if not frame.code_context:
            #                     continue

            #                 code_str = "".join(line for line in frame.code_context if line != '\n')
            #                 log_content += """File: "{filename}" Line: {line}\n{code}""".format(filename=frame.filename,
            #                                                                                    line=frame.lineno,
            #                                                                                    code=code_str)

            #         log_content += "\n***********************************"
            #         _logger.error(log_content)
            #         _logger.error("删除 general_code")
            res = self.cli.delete(*names)
        except Exception as e:
            return False, str(e)

        return True, res

    def delete_name_re(self, re_str):
        key_list = self.cli.keys(re_str)
        if not key_list:
            return True, None
        # if 'general_code' in re_str:
        #     import inspect
        #     frame_list = inspect.getouterframes(inspect.currentframe(), 3)
        #     log_content = "***********************************\n"
        #     for frame in frame_list:
        #         if 'woltu_addons' in frame.filename:
        #             log_content += frame.filename + "\n"
        #             if not frame.code_context:
        #                 continue

        #             code_str = "".join(line for line in frame.code_context if line != '\n')
        #             log_content += """File: "{filename}" Line: {line}\n{code}""".format(filename=frame.filename,
        #                                                                                 line=frame.lineno,
        #                                                                                 code=code_str)

        #     log_content += "\n***********************************"
        #     _logger.error(log_content)
        #     _logger.error("删除 general_code")

        _logger.info("del %s" % ','.join(str(key) for key in key_list))
        try:
            for key in key_list:
                if key:
                    res = self.cli.delete(key)
        except Exception as e:
            return False, str(e)

        return True, True

    def exists_name(self, name):
        try:
            res = self.cli.exists(name)
        except Exception as e:
            return False, str(e)

        return True, res

    # def type_name(self, name):
    #     try:
    #         res = self.cli.type(name)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res
    #
    # def clear_db(self):
    #     try:
    #         res = self.cli.flushdb()
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res
    #
    # def get_keys(self, re_str="*"):
    #     try:
    #         res = self.cli.keys(re_str)
    #     except Exception as e:
    #         return False, str(e)
    #
    #     return True, res

    def select_db(self, index):
        try:
            res = self.cli.select(index)
        except Exception as e:
            return False, "切换数据库失败[%s]" % str(e)

        return True, res

    def close(self):
        try:
            res = self.cli.close()
        except Exception as e:
            return False, "关闭数据库失败[%s]" % str(e)

        return True, res

    def redis_info(self, key):
        try:
            res = self.cli.info(key)
        except Exception as e:
            return False, "查看数据库信息失败[%s]" % str(e)

        return True, res

class RedisPoolManager(object):
    def __init__(self, **kwargs):
        self.pool = redis.ConnectionPool(**kwargs)

    def get_cli(self, db=0):
        return RedisOperate(redis.Redis(connection_pool=self.pool), db=db)

    def test_cli(self):
        cli = redis.Redis(connection_pool=self.pool)
        try:
            _logger.info(cli.info("Server"))
            _logger.info("Redis 已经连接")
        except Exception as e:
            _logger.info("Redis 连接失败: %s" % str(e))
            raise

    def close_cli(self):
        return self.pool.disconnect()




