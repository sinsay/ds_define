import typing

from .ds_base import Operator
from ...util import EnumBase


class And(EnumBase):

    @staticmethod
    def value() -> int:
        return 1


class Or(EnumBase):

    @staticmethod
    def value() -> int:
        return 2


PipeLogic = typing.Union[typing.Type[And], typing.Type[Or], And, Or]


class PipeNode(object):
    def __init__(self, *datasource: Operator,
                 logic: PipeLogic = And,
                 result_as: typing.Union[str, None] = None):
        self.datasource = datasource
        self.logic = logic
        self.result_as = result_as


class Pipe(object):
    And = And
    Or = Or

    """
    Pipe 定义了用于配置管道操作的定义接口，
    通过该接口可以定义各个 DataSource 或者 Operator
    """

    def __init__(self, *datasource: Operator,
                 logic: PipeLogic = And,
                 result_as: typing.Union[str, None] = None):
        """
        datasource 是一系列 Operator，每个 Operator 都是一个数据库操作
        result_as 表示 datasource 的操作结果是否需要作为结果，传递给下一步的
        操作
        """
        self.nodes = [PipeNode(*datasource, logic=logic, result_as=result_as)]

    def next(self, *datasource: Operator,
             logic: PipeLogic = And,
             result_as: typing.Union[str, None] = None):
        """
        添加下一步的操作
        """
        self.nodes.append(
            PipeNode(*datasource, logic=logic, result_as=result_as)
        )
        return self
