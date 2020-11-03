import enum

from .type_error import *
from .type_valid_base import Validate, EmptyValidate, fail


class ArgSource(enum.Enum):
    UNKNOWN = "UNKNOWN"
    HEADER = "HEADER"
    BODY = "BODY"
    PARAMS = "PARAMS"
    PATH = "PATH"
    RPC = "RPC"


def default_extractor(v):
    return v


class ColumnInfo(object):
    """
    数据库列定义信息，包括了与数据库匹配的一系列参数配置，主要用于在创建
    数据模型定义时保持与数据库一致，或者是利用这些配置信息来管理跟踪对应
    的数据库表
    """

    def __init__(
            self,
            primary_key: bool = False,
            nullable: bool = False,
            index: bool = False,
            unique: bool = False,
            length: int = None,
            foreign: str = None,
    ):
        self._primary_key: bool = primary_key
        self._nullable: bool = nullable
        self._index: bool = index
        self._unique: bool = unique
        self._length: int = length
        self._foreign: str = foreign
        self._column_type: str = ""
        self._name: str = ""

    def primary(self, primary_key: bool = True):
        """
        设置是否为主键
        :param primary_key:
        :return:
        """
        self._primary_key = primary_key
        return self

    def nullable(self, nullable: bool = True):
        """
        设置是否可为空
        :param nullable:
        :return:
        """
        self._nullable = nullable
        return self

    def index(self, index: bool = True):
        """
        设置是否建立索引
        :param index:
        :return:
        """
        self._index = index
        return self

    def unique(self, unique: bool = True):
        """
        设置是否唯一
        :param unique:
        :return:
        """
        self._unique = unique
        return self

    def length(self, length: int):
        """
        设置长度
        :param length:
        :return:
        """
        self._length = length
        return self

    def foreign(self, foreign: str):
        """
        设置外键信息
        :param foreign:
        :return:
        """
        self._foreign = foreign
        return self

    def type(self, column_type: str):
        """
        设置字段类型
        :param column_type:
        :return:
        """
        self._column_type = column_type
        return self

    def name(self, name: str):
        self._name = name

    def update(self, other: 'ColumnInfo'):
        """
        使用 other 更新自己
        """
        for attr_name in dir(self):
            attr = getattr(other, attr_name, None)
            if attr is None:
                continue

            setattr(self, attr_name, attr)

    def get_name(self) -> str:
        return self._name

    def get_foreign(self) -> typing.Union[None, str]:
        return self._foreign

    def get_length(self) -> int:
        return self._length

    def get_unique(self) -> bool:
        return self._unique

    def get_index(self) -> bool:
        return self._index

    def get_nullable(self) -> bool:
        return self._nullable

    def get_primary(self) -> bool:
        return self._primary_key

    def get_type(self) -> str:
        """
        获取当前 Column 在 SQLAlchemy 中对应的类型定义
        """
        if not self._column_type:
            raise ValueError("The type of ColumnInfo can not be null.")
        return self._column_type

    def __repr__(self):
        return f"<ColumnInfo: name: {self.get_name()}, primary_key: {self.get_primary()}, " \
               f"nullable: {self.get_nullable()}, index: {self.get_index()}, unique: {self.get_unique()}, " \
               f"length: {self.get_length()}, foreign: {self.get_foreign()}, type: {self.get_type()}>"


class IndexInfo(object):
    """
    设置索引字段信息
    """
    BTREE, HASH = 'btree', 'hash'

    def __init__(
            self,
            index_name: str = '',
            columns: list = None,
            index_type: str = BTREE,
            prefix: str = '',
            *_args,
            **_kwargs
    ):
        self.columns: list = columns
        self.index_type: str = index_type

        self.index_name = 'ind_{}'.format('_'.join(columns)) if not index_name else index_name
        if prefix:
            self.index_name = f'{prefix}_{self.index_name}'

    @staticmethod
    def get_type() -> str:
        """
        获取当前 Column 在 SQLAlchemy 中对应的类型定义
        """
        return 'table_index'

    def __repr__(self):
        return f"<IndexInfo: columns: ({','.join(self.columns)}), index_name: {self.index_name}, " \
               f"index_type: {self.index_type}>"


class RpcType(object):
    """
    Common 库提供的基础类型定义基类，继承了该类的类型，可用于 RPC 接口或 Flask 服务的参数定义。
    也可用于定义数据库模型，后续可使用 RPC Generator 生成对应与 SQLAlchemy 的 ORM 代码，利用 SQLAlchemy
    提供的能力，能够提供所有 ORM 的操作接口及数据库自动生成等能力
    """
    __rpc_tag__ = "R"
    default_error_messages = {
        ERROR_TYPE.null: '{field} is required, but value is {value}'
    }

    def __init__(self, default_value, required: bool, description: str = "",
                 validator: Validate = None, validate_extractor=None, origin=None,
                 load_only=True, dump_only=True, *args, **kwargs):
        """
        @param default_value: 默认值
        @param required: 是否必须
        @param description: 描述文档
        @param validator: 检查器, 用于对参数做自定义检查
        @param origin: 指定该字段是某原始字段的别名
        """
        self.default_value = default_value
        self.required = required
        self.description = description or ""
        self.validate_extractor = validate_extractor
        self.validator = validator or EmptyValidate()
        self._source: ArgSource = ArgSource.UNKNOWN
        self._is_column = False
        self._column_info: ColumnInfo = ColumnInfo()
        if self.validator:
            self.validator.set_host(self)

        self.error_messages = ""
        self.collection_err_msg()

        self.origin = origin
        self.load_only = load_only
        self.dump_only = dump_only

    def get_type(self):
        raise Exception("RpcType 是虚拟基类，要获得具体类型需调用具体类型的实现")

    def collection_err_msg(self):
        # Collect default error message from self and parent classes
        messages = {}
        for cls in reversed(self.__class__.__mro__):
            messages.update(getattr(cls, 'default_error_messages', {}))
        self.error_messages = messages

    def fail(self, key, **kwargs):
        """
        A helper method that simply raises a validation error.
        """
        return fail(self, key, **kwargs)

    def valid(self, name: str, value):
        if self.required and value is None:
            self.fail(ERROR_TYPE.null, field=name, value=value)

        if value is not None and not type(value).__name__ == self.get_type():
            self.fail(ERROR_TYPE.invalid, input_type=type(value).__name__)

    def valid_with_validator(self, _name, value):
        if value is None and not self.required:
            return
        extractor = self.validate_extractor or default_extractor
        if self.validator:
            self.validator.valid(extractor(value))

    def column(
            self,
            primary_key: bool = False,
            nullable: bool = False,
            index: bool = False,
            unique: bool = False,
            length: int = None,
            foreign: str = None,
            column: typing.Union[ColumnInfo, None] = None
    ):
        """
        将该字段转换为数据库字段，当调用了该函数后，Generator 会为包含了该字段的 Model 创建
        对应的 ORM 定义
        @param primary_key: 该字段是否未主键
        @param nullable: 该字段是否可为空
        @param index: 该字段是否需要索引
        @param unique: 该字段是否设置唯一
        @param length: 该字段的长度
        @param foreign: 该字段如果为外键，填写的是其主表的字段名，如 XXTable.id
        @param column: 该字段的列信息，如果传递了列信息，则将全部使用列信息中的定义
        """
        self._is_column = True
        ci = ColumnInfo(
            primary_key=primary_key,
            nullable=nullable,
            index=index,
            unique=unique,
            length=length,
            foreign=foreign,
        )

        ci.type(self.get_column_type())

        if column:
            ci = column
        self._column_info.update(ci)
        return self

    def source(self, st: ArgSource):
        self._source = st
        return self

    def get_source(self) -> ArgSource:
        return self._source

    def get_column_type(self):
        """
        获取 RpcType 的 column_type 字段, 每个继承了 RpcType 的类型重写该方法，返回 SQLAlchemy 对应的类型名
        """
        raise NotImplementedError("type inherit from RpcType, must implement get_column_type.")

    def is_column(self):
        return self._is_column

    def rm_column(self):
        self._is_column = False
        return self

    def get_column(self) -> ColumnInfo:
        """
        获取字段定义信
        """
        if not self._is_column:
            raise AttributeError(f"Field haven't set as column.")

        col_type = self.get_column_type()
        self._column_info.column_type = col_type
        return self._column_info

    def serialize(self, value: any) -> any:
        raise NotImplementedError('Type:`{}` not implement serialize method.'.format(self))

    def deserialize(self, value: any) -> any:
        raise NotImplementedError('Type:`{}` not implement deserialize method.'.format(self))
