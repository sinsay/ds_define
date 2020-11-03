class EnumBase(object):
    @staticmethod
    def value() -> int:
        raise NotImplemented

    @classmethod
    def name(cls) -> str:
        return cls.__name__
