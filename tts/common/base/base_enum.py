from enum import Enum as __Enum, unique


class BaseEnum(__Enum):
    @classmethod
    def values(cls):
        return tuple(item.value for item in cls.__members__.values())

    @classmethod
    def names(cls):
        return tuple(item.name for item in cls.__members__.values())

    @classmethod
    def value_dict(cls):
        return {item.name: item.value for item in cls.__members__.values()}

    @classmethod
    def get_name(cls, code):
        return cls.value_dict().get(code)

    @classmethod
    def get_value(cls, name):
        for key, value in cls.value_dict().items():
            if key == name:
                return value

        raise Exception("没有此name[%s]" % name)

    @classmethod
    def in_codes(cls, code):
        return True if code in cls.values() else False

    @classmethod
    def in_names(cls, name):
        return True if name in cls.names() else False
