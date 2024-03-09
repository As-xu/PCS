import os


def make_dirs(dir_list):
    for d in dir_list:
        try:
            os.makedirs(d, exist_ok=True)
        except Exception as e:
            raise Exception("创建目录失败[%s]" % e)