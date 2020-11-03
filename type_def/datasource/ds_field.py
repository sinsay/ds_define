import typing

from type_def.type_base import ColumnInfo


class OpTag(object):
    Equal: str = "eq"
    NotEqual: str = "ne"
    Less: str = "l"
    LessOrEqual: str = "le"
    Greater: str = "g"
    GreaterOrEqual: str = "ge"
    In: str = "in"
    NotIn: str = "ni"

    Like: str = "like"

    And = "and"
    Or = "or"

    _Operator = [Equal, NotEqual, Less, LessOrEqual, Greater, GreaterOrEqual, In, NotIn]
    _Logical = [And, Or]

    @staticmethod
    def is_logical(tag: str) -> bool:
        return tag in OpTag._Logical

    @staticmethod
    def is_operator(tag: str) -> bool:
        return tag in OpTag._Operator


class FieldMode:
    Normal = 1
    Count = 2
    Sum = 3


class ModelField(object):
    def __init__(self, model, col: ColumnInfo):
        self._model = model
        self._col = col
        self._alias = ""
        self._mode = FieldMode.Normal

    def get_model(self):
        return self._model

    def get_alias(self) -> str:
        return self._alias or self._col.get_name()

    def get_column(self) -> ColumnInfo:
        return self._col

    def get_mode(self):
        return self._mode

    def alias(self, alias: str) -> 'ModelField':
        """
        设置字段别名, 设置之后的别名只会在生成类型时起作用，并不会在生成 ORM 或 SQL 语句
        时造成任何影响
        :param alias:
        :return:
        """
        self._alias = alias
        return self

    def count(self):
        """
        对当前的 Field 进行 Count 统计
        """
        self._mode = FieldMode.Count
        return self

    def sum(self):
        """
        对当前的 Field 进行 Sum 统计
        """
        self._mode = FieldMode.Sum
        return self

    def same(self, other: 'ModelField') -> bool:
        return self._model.get_name() == other._model.get_name() and \
               self._col.name == other._col.name and \
               self._alias == other._alias

    def eq(self, other: 'FieldOrAny') -> 'ModelFieldOp':
        return self.__eq__(other)

    def ne(self, other: 'FieldOrAny') -> 'ModelFieldOp':
        return self.__ne__(other)

    def le(self, other: 'FieldOrAny') -> 'ModelFieldOp':
        return self.__le__(other)

    def lt(self, other: 'FieldOrAny') -> 'ModelFieldOp':
        return self.__lt__(other)

    def gt(self, other: 'FieldOrAny') -> 'ModelFieldOp':
        return self.__gt__(other)

    def ge(self, other: 'FieldOrAny') -> 'ModelFieldOp':
        return self.__ge__(other)

    def like(self, other: 'FieldOrAny') -> 'ModelFieldOp':
        return check_type(OpTag.Like, self, other)

    def in_(self, other: 'FieldOrAny') -> 'ModelFieldOp':
        return check_type(OpTag.In, self, other)

    def not_in(self, other: 'FieldOrAny') -> 'ModelFieldOp':
        return check_type(OpTag.In, self, other)

    def __eq__(self, other: 'FieldOrAny') -> 'ModelFieldOp':
        return check_type(OpTag.Equal, self, other)

    def __ne__(self, other: 'FieldOrAny') -> 'ModelFieldOp':
        return check_type(OpTag.NotEqual, self, other)

    def __le__(self, other: 'FieldOrAny') -> 'ModelFieldOp':
        return check_type(OpTag.LessOrEqual, self, other)

    def __lt__(self, other: 'FieldOrAny') -> 'ModelFieldOp':
        return check_type(OpTag.Less, self, other)

    def __gt__(self, other: 'FieldOrAny') -> 'ModelFieldOp':
        return check_type(OpTag.Greater, self, other)

    def __ge__(self, other: 'FieldOrAny') -> 'ModelFieldOp':
        return check_type(OpTag.GreaterOrEqual, self, other)


def check_type(tag: str, a: 'FieldOrAny', b: 'FieldOrAny') -> 'ModelFieldOp':
    # TODO check type
    if tag == OpTag.In:
        pass
    return ModelFieldOp(tag, a, b)


OpNode = typing.Union[ModelField, 'ModelFieldOp', 'ArgItem', typing.Any]


class ModelFieldOp(object):
    def __init__(
            self, tag: str,
            left: OpNode,
            right: OpNode
    ):
        self._tag = tag
        self._left = left
        self._right = right

    def __and__(self, other: 'ModelFieldOp') -> 'ModelFieldOp':
        return ModelFieldOp(OpTag.And, self, other)

    def __or__(self, other: 'ModelFieldOp') -> 'ModelFieldOp':
        return ModelFieldOp(OpTag.Or, self, other)

    def get_left(self) -> OpNode:
        return self._left

    def get_right(self) -> OpNode:
        return self._right

    def get_tag(self) -> OpNode:
        return self._tag

    def is_logical(self) -> bool:
        return OpTag.is_logical(self.get_tag())

    def is_operator(self) -> bool:
        return OpTag.is_operator(self.get_tag())

    @staticmethod
    def empty() -> 'ModelFieldOp':
        return ModelFieldOp(OpTag.Equal, 1, 1)


class ArgItem(object):
    def __init__(self, from_key: str, prev: typing.Union[None, 'ArgItem'] = None):
        self._prev: typing.Union[None, ArgItem] = prev
        self._from_key = from_key
        self._nth = -1

    def __getattr__(self, item: str) -> 'ArgItem':
        return ArgItem(item, self)

    def nth(self, n: int) -> 'ArgItem':
        self._nth = n
        return self


class Args(object):
    """
    占位符，用于告知解析器 DataSource 中的某些依赖需要从请求的参数中获取
    """

    def __getattr__(self, item: str) -> ArgItem:
        return ArgItem(item)


args = Args()

FieldOrAny = typing.Union[ModelField, typing.Any]
