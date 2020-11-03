import typing

from .ds_base import DataSource, Operator
from .ds_error import DataSourceEmptyError, DataSourceInvalidError
from .ds_field import ModelField, ModelFieldOp


class SQLInfo(object):
    """
    SQL 语句解析结果
    """

    def __init__(self, ds: 'DataSource'):
        """
        解析 ds 中所保存的定义信息，并将其保存为解析好的 select、where、join、paging 信息
        :param ds:
        """
        self._select: typing.List[ModelField] = []
        self._where: ModelFieldOp = ModelFieldOp.empty()
        self._join: typing.List[ModelFieldOp] = []
        self._skip = 0
        self._take = 0

        self.analyse(ds)

    def append_select(self, field: ModelField):
        self._select.append(field)

    def set_where(self, where: ModelFieldOp):
        self._where = where

    def append_join(self, join: ModelFieldOp):
        self._join.append(join)

    def set_paging(self, skip: int, take: int):
        self._skip = skip
        self._take = take

    def analyse(self, ds: 'DataSource'):
        """
        解析 ds 中的表达式，后续的各种优化都可以在这里进行处理
        :param ds:
        :return:
        """
        exps = ds.get_exps()
        if not exps:
            raise DataSourceEmptyError("Can not analyse DataSource without expression!")

        op: Operator = exps.pop()
        op.analyse()

        if not self._select:
            raise DataSourceInvalidError("Can not configure the DataSource without Select Expression")

    @property
    def select(self):
        return self._select

    @property
    def where(self):
        return self._where

    @property
    def join(self):
        return self._join

    @property
    def paging(self):
        return self._skip, self._take
