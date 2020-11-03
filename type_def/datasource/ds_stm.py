"""
本模块用于支持定义基础的数据库操作描述，后续 Generator 会通过该描述
信息生成数据库查询操作，避免开发人员重复实现基本的业务逻辑，并且可通过定义信息也
能够直观的看出对应的数据接口会触发的具体操作
"""

from type_def.datasource.ds_base import DataSource, Operator
from type_def.datasource.ds_field import ModelField, ModelFieldOp, OpTag

from type_def.type_error import *
from type_def.type_check import is_model
from util import EnumBase

SelectField = typing.Union[ModelField, typing.Any]


class LeftJoin(EnumBase):
    @staticmethod
    def value() -> int:
        return 1


class InnerJoin(EnumBase):
    @staticmethod
    def value() -> int:
        return 2


class OuterJoin(EnumBase):
    @staticmethod
    def value() -> int:
        return 3


JoinMode = typing.Union[typing.Type[LeftJoin], typing.Type[InnerJoin], typing.Type[OuterJoin]]


class AllowAlias(Operator):
    """
    允许状态机进入 Alias 模式，一般只会在子查询中以该模式结尾
    """

    def alias(self, alias: str) -> 'Alias':
        """
        为子查询的结果设置别名, 一般用于 Count 或者 Sum 之类的计算
        """
        return Alias(self.get_source(), alias)


class AllowFilter(Operator):
    """
    允许状态机进入 Filter 模式
    """

    def filter(self, filter_op: ModelFieldOp) -> 'Filter':
        """
        设置过滤条件
        :param filter_op:
        :return:
        """
        return Filter(self.get_source(), filter_op)


class AllowPaging(Operator):
    """
    允许状态机进入 Paging 模式
    """

    def skip(self, n: typing.Union[int, ModelField]) -> 'Paging':
        """
        跳过 N 条记录，N 可以是来自参数或其他表的数据
        :param n:
        :return:
        """
        return Paging(self.get_source()).skip(n)

    def take(self, n: typing.Union[int, ModelField]) -> 'Paging':
        """
        获取 N 条记录，N 可以是来自参数或其他表的数据
        :param n:
        :return:
        """
        return Paging(self.get_source()).take(n)

    def first(self) -> 'Paging':
        """
        获取当前结果集中的第一条数据，该接口会导致当前结果集的返回结果被解析为
        单一值， 而不是默认的列表
        """
        return Paging(self.get_source()).take(1)

    def paging(self, page: typing.Union[int, ModelField], size: typing.Union[int, ModelField]):
        """
        可以用于快速配置分页功能
        合并 skip 及 take 的便捷接口
        :param page:
        :param size:
        :return:
        """
        return self.skip((page - 1) * size).take(size)


class AllowJoin(Operator):
    """
    允许状态机进入 Join 模式
    """

    def join(self, join_cond: ModelFieldOp, *more: ModelFieldOp, mode: JoinMode = LeftJoin) -> 'Join':
        """
        联表查询, join_cond 为来自 Model 的查询条件
        :param join_cond:
        :param more:
        :param mode:
        :return:
        """
        return Join(self.get_source()).join(join_cond, *more, mode=mode)


class AllowUpdate(AllowFilter):
    """
    允许进入 Update 状态
    """

    def update(self, update_field: ModelFieldOp, *more: ModelFieldOp) -> 'Updater':
        """
        进入 Update 状态, 并指定了需要进行 Update 的字段信息
        """
        return Updater(self.get_source(), update_field, *more)


class Updater(AllowFilter):
    def __init__(self, source: 'DataSource', update_field: ModelFieldOp, *more: ModelFieldOp):
        super(Updater, self).__init__(source)
        self._update_op = [update_field] + list(more)

    def update(self, update_field: ModelFieldOp, *more: ModelFieldOp) -> 'Updater':
        """
        指定需要更新的字段， update_field 及 more 都必须来自于同一个 Model
        """
        self._update_op = self._update_op + [update_field] + list(more)
        return self


class Filter(AllowPaging):
    """
    Filter 状态，提供了过滤接口，用于定义过滤数据的表达式
    """

    def __init__(self, source: 'DataSource', filter_op: ModelFieldOp):
        super(Filter, self).__init__(source)
        self._ops: typing.List[ModelFieldOp] = [filter_op] if filter_op else []

    def and_(self, filter_op: ModelFieldOp) -> 'Filter':
        """
        添加新的条件，并将新新条件与原条件使用 与 的关系建立关联
        :param filter_op:
        :return:
        """
        self._ops = ModelFieldOp(OpTag.And, self._ops, filter_op)
        return self

    def or_(self, filter_op: ModelFieldOp) -> 'Filter':
        """
        添加新的条件，并将新新条件与原条件使用 或 的关系建立关联
        :param filter_op:
        :return:
        """
        self._ops = ModelFieldOp(OpTag.Or, self._ops, filter_op)
        return self

    def quote(self) -> 'Filter':
        """
        将当前条件进行打包，便于建立复杂的逻辑关系
        :return:
        """


class Alias(Operator):
    """
    设置子查询的别名, 只能作为表达式的叶子节点
    """

    def __init__(self, source: 'DataSource', alias: str):
        super().__init__(source)
        self._alias = alias


class Select(AllowFilter, AllowPaging, AllowJoin, AllowAlias):
    """
    Select 状态，提供了搜索入口，在该状态下可以进入 Filter、Paging、Join 等状态
    """

    def __init__(self, source: 'DataSource', model_or_field: SelectField,
                 *more: SelectField):
        super(Select, self).__init__(source)
        self._select_info: typing.List[SelectField] = []
        self.select(model_or_field, *more)

    def select(self, model_or_field: SelectField, *more: SelectField) -> 'Select':
        """
        select more column or model
        :param model_or_field:
        :param more:
        :return:
        """
        new_field = [model_or_field] + list(more)
        for f in new_field:
            if is_model(f):
                # let the model initialize the column info
                f.get_columns()
            else:  # ModelField
                f.get_model().get_columns()

        self._select_info = self._select_info + new_field
        return self


class Join(AllowFilter, AllowPaging, AllowAlias):
    """
    Join 状态，用于提供链表查询定义的接口
    """

    def __init__(self, source: 'DataSource'):
        super(Join, self).__init__(source)
        self._join_info: typing.List[ModelFieldOp] = []
        self._join_mode: JoinMode = LeftJoin

    def join(self, join_cond: ModelFieldOp, *more: ModelFieldOp, mode: JoinMode = LeftJoin) -> 'Join':
        """
        联表查询, join_cond 为来自 Model 的查询条件, jin_cond 是 ModelFieldOp 类型，
        可直接使用 Model.field == xxx 作为 ModelFieldOp, 而无需再指定 join 的对象，
        因为从 op 中已经可以推断出对象
        在 Join 模式中，ModelFieldOp 的左操作数及右操作数都只能是 ModelField 而不能是其他
        占位符或立即数
        :param join_cond:
        :param more:
        :param mode:
        :return:
        """
        self._join_info = self._join_info + [join_cond] + list(more)
        self._join_mode = mode
        return self


class Paging(AllowAlias):
    """
    Paging 状态，用于提供分页接口
    """

    def __init__(self, source: 'DataSource'):
        super(Paging, self).__init__(source)
        self._n = -1
        self._single = False

    def skip(self, n: typing.Union[int, ModelField]) -> 'Paging':
        """
        跳过 N 条记录， N 可以是来自参数或其他表的数据
        :param n:
        :return:
        """
        self._n = n
        return self

    def take(self, n: typing.Union[int, ModelField]) -> 'Paging':
        """
        获取 N 条记录，N 可以是来自参数或其他表的数据
        :param n:
        :return:
        """
        self._n = n
        return self

    def first(self) -> 'Paging':
        """
        只获取数据结果集中的第一个, 这会导致获取的结果集被处理为一个单一的对象，
        而不是默认的列表
        """
        self._n = 1
        self._single = True
        return self


class EntryDataSource(DataSource):
    """
    数据操作定义类型，该类型提供了基础的数据定义接口, 及数据源操作的入口 Select
    """

    def select(self, model: SelectField, *join_models: SelectField) -> Select:
        s = Select(self, model, *join_models)
        return s

    def update(self, update_field: ModelFieldOp, *more: ModelFieldOp) -> Updater:
        u = Updater(self, update_field, *more)
        return u
