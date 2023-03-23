from enum import Enum as __Enum, unique


class BaseEnum(__Enum):
    @classmethod
    def codes(cls):
        return tuple(item.value[0] for item in cls.__members__.values())

    @classmethod
    def names(cls):
        return tuple(item.value[1] for item in cls.__members__.values())

    @classmethod
    def value_dict(cls):
        return {item.value[0]: item.value[1] for item in cls.__members__.values()}

    @classmethod
    def get_name(cls, code):
        return cls.value_dict().get(code)

    @classmethod
    def in_codes(cls, code):
        return True if code in cls.codes() else False

    @classmethod
    def in_names(cls, name):
        return True if name in cls.names() else False

    @property
    def code(self):
        return self.value[0]

    @property
    def show(self):
        return self.value[1]