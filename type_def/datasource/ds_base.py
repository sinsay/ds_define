import typing


class Operator:
    """
    操作基类，所有的 DataSource 接口都需要继承该基类
    """

    __tag__ = None

    def is_tag(self, tag: str) -> bool:
        """
        判断操作基类是否指定类型
        """
        if not self.__tag__:
            raise NotImplementedError(
                f"The Operator {type(self)} Need Implement the logic and set the tag to an unique identifier")

        return self.__tag__ == tag

    def __init__(self, source: 'DataSource'):
        self._source = source
        self._source.add_exp(self)

    def get_source(self) -> 'DataSource':
        return self._source

    def analyse(self):
        raise NotImplemented


class DataSource(object):
    """
    数据操作定义类型，该类型提供了基础的数据定义接口
    """

    def __init__(self):
        self._ops: typing.List[Operator] = []

    def add_exp(self, exp: Operator):
        self._ops.append(exp)

    def get_exps(self) -> typing.List[Operator]:
        return self._ops
