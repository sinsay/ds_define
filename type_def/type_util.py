"""
    该包主要是为 rpc 公共库提供一个通用的类型注解机制
    提供的函数会尽量贴近原有 flask 接口，便于旧接口的升级
"""

import copy
import datetime

from flask_restplus import fields as f_fields

from . import type_def, RpcType
from . import db_extend
from . import datasource as stm
from .type_tags import *
from .type_base import ColumnInfo, IndexInfo
from .type_valid import validator_constructor, StringValidate, DictValidate, \
    ListValidate, ChoiceValidate
from .type_error import ModelValidationError
from .datasource import ModelField, ArgItem, Pipe, Loop


class Model(object):
    """
    数据模型定义
    """

    __model_tag__ = "MT"

    def __init__(self, name: str, fs: typing.Dict[str, RpcType], description: str = "",
                 indexes: typing.List[IndexInfo] = None):
        """
        :param name:
        :param fs:
        :param description:
        :param indexes: 索引类 list

        添加索引 2 种方式:

        ```python
        User = fields.model("she_user", {
            "id": fields.Integer(description="xxx").column(primary_key=True, index=True),
            "name": fields.String().column(length=32),
            "other": fields.Float().column()
        },
        description="user table",
        indexes=[fields.index('ind_id_name', columns=['id', 'name'], index_type=fields.index.HASH)])
        or
        User.add_indexes([fields.index(columns=['id', 'other'])])
        ```

        """
        d = _dict(fs, description)
        self._name = name
        self._fs: type_def.Dict = d
        self._indexes: typing.List[IndexInfo] = []
        if indexes:
            self.add_indexes(indexes)

        # 用来标识该 model 是参数还是返回值
        self._type = None

    def get_name(self):
        return super(Model, self).__getattribute__("_name")

    def get_fields(self) -> type_def.Dict:
        return super(Model, self).__getattribute__("_fs")

    def get_indexes(self) -> typing.List[IndexInfo]:
        return super(Model, self).__getattribute__("_indexes")

    def get_type(self):
        return super(Model, self).__getattribute__("_type")

    def __getattr__(self, item: str) -> ModelField:
        """
        用于获取已经添加的字段信息，用户后续支持 DataSource 的配置
        :param item:
        :return:
        """
        elem_info = self.get_fields().get_elem_info()
        col = elem_info.get(item, None)
        if col:
            return ModelField(self, col.get_column())

        try:
            return super(Model, self).__getattribute__(item)
        except AttributeError:
            raise AttributeError(f"尝试从 Model {self.get_name()} 中获取不存在的字段 {item}")

    def as_args(self, path_str: str = "") -> typing.List[ArgItem]:
        """
        将当前 Model 中的所有字段转换为参数, 当字段在参数的嵌套字段中时，可以配置访问的路径 path
        :return:
        """
        path = path_str.split(".")
        path_arg = None
        if path:
            path_arg = ArgItem(path[0])
            for p in path[1:]:
                path_arg = ArgItem(p, path_arg)

        arg_list = []
        elem_info = self.get_fields().get_elem_info()
        for k in elem_info.keys():
            arg_list.append(ArgItem(k, path_arg))

        return arg_list

    def extend(self, field_name: str, field_type: RpcType):
        """
        扩展 model，在当前 Model 的基础上构建一个新的 Model，
        并为其增加 类型为 field_type 的字段 field_name
        """
        m2 = copy.deepcopy(self)
        m2.get_fields().add_field(field_name, field_type)
        return m2

    def extend_model(self, model: 'Model', rm_column_info: bool = True):
        """
        扩展 model, 在当前 Model 的基础上构建一个新的 Model,
        并将参数 m 中的字段信息复制到新的 Model 中
        """
        # 被用来扩展的 Model 会被移除 ORM 信息，防止解析到重复的表定义
        m2 = copy.deepcopy(self)
        for k, v in model.get_fields().get_elem_info().items():
            v = copy.deepcopy(v)
            if rm_column_info:
                v.rm_column()

            m2.get_fields().add_field(k, v)

        return m2

    def extend_to_db_model(self, model: 'Model'):
        m2 = copy.deepcopy(self)
        for k, v in model.get_fields().get_elem_info().items():
            m2.get_fields().add_field(k, copy.deepcopy(v))

        return m2

    def get_columns(self) -> typing.List[ColumnInfo]:
        """
        获取该模型的数据库字段定义
        """
        cols = []
        for name, field in self.get_fields().get_elem_info().items():
            if not field.is_column():
                continue
            col: ColumnInfo = field.get_column()
            col.name(name)
            cols.append(col)

        return cols

    def _check_index(self, indexes: typing.List[IndexInfo] = None, db_type: str = MYSQL):
        """检测索引正确性:
        1.索引所使用字段非空性
        2.索引类型是否是数据库支持的
        3.索引是否包含非表字段
        """
        cols = self.get_columns()
        for index in indexes:
            if not index.columns:
                raise ModelValidationError(
                    f"model {self.get_name()}'s index {index.index_name} can no without any column.")
            if index.index_type not in SUPPORT_INDEX_TYPES[db_type]:
                raise Exception(
                    f'{db_type} not support index type :{index.index_type},'
                    f'please choice ({",".join(SUPPORT_INDEX_TYPES[db_type])})) ')
            for index_column in index.columns:
                if index_column not in set([col.name for col in cols]):
                    raise Exception(f'the column:{index_column} not defined in this table:{self.get_name()}')

    def _aggr_indexes(self, old_indexes: typing.List[IndexInfo] = None, new_indexes: typing.List[IndexInfo] = None):
        """如果本身model有indexes,则后者覆盖前者,以 columns列表为主;
        如果本身 column 有字段 index=True,以 column 定义为主,避免重复定义
        """
        old_indexes_c = copy.deepcopy(old_indexes) or []
        new_indexes_column = [new_index.columns for new_index in new_indexes]
        cur_indexes = new_indexes + [old_index for old_index in old_indexes_c if
                                     old_index.columns not in new_indexes_column]
        column_indexes_name = [[col.name] for col in self.get_columns() if col.index]
        return [cur_index for cur_index in cur_indexes if cur_index.columns not in column_indexes_name]

    def add_indexes(self, indexes: typing.List[IndexInfo] = None):
        """为表额外添加索引,可添加复合索引,可设置索引的类型"""
        if not self.get_columns():
            raise ModelValidationError(f"model {self.get_name()} has no column, shouldn't add indexes for it.")
        indexes = indexes or []
        self._check_index(indexes)
        self._indexes = self._aggr_indexes(self._indexes, indexes)

    def set_required(self, fields_list: typing.List[str], is_required: bool):
        """
        覆盖Model中的必传参数
        """
        # 被用来扩展的 Model 会被移除 ORM 信息，防止解析到重复的表定义
        m2 = copy.deepcopy(self)
        for field in fields_list:
            field_type = self.get_fields().type_dict.get(field, None)
            if field_type is None:
                raise TypeError("Not exists field:`{}` define".format(field))
            setattr(field_type, "required", is_required)
        return m2

    def only_required(self, fields_list: typing.List[str]):
        return self.set_required(fields_list, is_required=True)

    def cancel_required(self, fields_list: typing.List[str]):
        return self.set_required(fields_list, is_required=False)

    def choose(self, field_list: typing.List[str]):
        """
        挑选某些字段，行程新的fields.Model
        """
        m2 = copy.deepcopy(self)
        m2.get_fields().type_dict = self.iter_serializer(
            self.get_fields().get_elem_info(), include=field_list
        )
        return m2

    def exclude(self, field_list: typing.List[str]):
        """
        排除某些字段，行程新的fields.Model
        """
        m2 = copy.deepcopy(self)
        m2.get_fields().type_dict = self.iter_serializer(self.get_fields().get_elem_info(), exclude=field_list)
        return m2

    def exclude_primary(self) -> 'Model':
        """
        移除当前 Model 的主键后返回新的 Model
        :return:
        """
        m2 = copy.deepcopy(self)
        m2.get_fields().clear_field()

        for k, v in m2.get_fields().get_elem_info().items():
            is_column: bool = v.is_column()
            if is_column:
                col: ColumnInfo = v.get_column()
                if col.get_primary():
                    continue
            m2.get_fields().add_field(k, v)

        return m2


def _model(name: str, fs: typing.Dict[str, RpcType], description: str = "",
           indexes: typing.List[IndexInfo] = None):
    """
    创建一个数据模型
    :param name:
    :param fs:
    :param description:
    :param indexes:索引信息
    :return:
    """
    return Model(name, fs, description, indexes)


def wrap(t: str, m: typing.Union[Model, RpcType]):
    # 只有 result type 会是 RpcType，因为只有 result 才能够不具有名称
    if isinstance(m, RpcType) and t == "args":
        raise Exception("参数定义必须有名称，args 不能与 RpcType 同时使用.")

    if isinstance(m, Model):
        m = m.get_fields()

    def w(cls):
        # doc 只加在原始的函数上
        while hasattr(cls, "__wrapped__"):
            cls = cls.__wrapped__

        setattr(cls, "_rpc_doc_%s" % t, m)
        return cls

    return w


def args(m: Model):
    """
    创建一个服务的参数描述
    :param m:
    :return:
    """
    return wrap("args", m)


def resp(m: typing.Union[Model, RpcType]):
    """
    创建一个服务的返回值描述
    :param m:
    :return:
    """
    return wrap("resp", m)


def _integer(description: str = "", required: bool = True,
             minimum: int = None, maximum: int = None,
             default_value: int = None, origin: str = None,
             desc: str = "", **kwargs) -> type_def.Integer:
    """
    创建一个 integer 类型
    :param description:
    :param required:
    :param minimum
    :param maximum
    :param default_value
    :param desc
    :return:
    """
    description = desc or description
    return type_def.Integer(
        default_value, required, description, origin=origin,
        validator=validator_constructor(min=minimum, max=maximum), **kwargs
    )


def _float(description: str = "", required: bool = True,
           minimum: float = None, maximum: float = None,
           default_value: float = None, origin: str = None,
           desc: str = "", **kwargs) -> type_def.Float:
    """
    创建一个浮点数类型
    :param description:
    :param required:
    :param minimum
    :param maximum
    :param default_value
    :return:
    """
    description = desc or description
    return type_def.Float(
        default_value, required, description, origin=origin,
        validator=validator_constructor(min=minimum, max=maximum, **kwargs)
    )


def _double(description: str = "", required: bool = True,
            minimum: float = None, maximum: float = None,
            default_value: float = None, origin: str = None,
            desc: str = "", **kwargs) -> type_def.Double:
    """
    创建一个 Double 类型
    :param description:
    :param required:
    :param minimum
    :param maximum
    :param default_value
    :return:
    """
    description = desc or description
    return type_def.Double(
        default_value, required, description, origin=origin,
        validator=validator_constructor(min=minimum, max=maximum, **kwargs)
    )


def _time(description: str = "", required: bool = True,
          minimum: float = None, maximum: float = None,
          in_format: str = None, out_format: str = None,
          default_value: datetime.time = None, origin: str = None,
          desc: str = "", **kwargs) -> type_def.Time:
    """
    创建一个 Time 类型, WARN: 该类型只能表示时间戳
    :param description:
    :param required:
    :param minimum
    :param maximum
    :param default_value
    :param desc
    :return:
    """
    description = desc or description
    return type_def.Time(
        default_value, required, description, origin=origin,
        in_format=in_format, out_format=out_format,
        validator=validator_constructor(min=minimum, max=maximum), **kwargs
    )


def _date(description: str = "", required: bool = True,
          minimum: float = None, maximum: float = None,
          in_format: str = None, out_format: str = None,
          default_value: datetime.date = None, origin: str = None,
          desc: str = "", **kwargs) -> type_def.Date:
    """
    创建一个 Date 类型, WARN: 该类型只能表示时间戳
    :param description:
    :param required:
    :param minimum
    :param maximum
    :param default_value
    :param desc
    :return:
    """
    description = desc or description
    return type_def.Date(
        default_value, required, description,
        in_format=in_format, out_format=out_format, origin=origin,
        validator=validator_constructor(min=minimum, max=maximum), **kwargs
    )


def _datetime(description: str = "", required: bool = True,
              minimum: float = None, maximum: float = None,
              in_format: str = None, out_format: str = None,
              default_value: datetime.datetime = None, origin: str = None,
              desc: str = "", **kwargs) -> type_def.DateTime:
    """
    创建一个 DateTime 类型, WARN: 该类型只能表示时间戳
    :param description:
    :param required:
    :param minimum
    :param maximum
    :param default_value
    :param desc
    :return:
    """
    description = desc or description
    return type_def.DateTime(
        default_value, required, description,
        in_format=in_format, out_format=out_format, origin=origin,
        validator=validator_constructor(min=minimum, max=maximum), **kwargs
    )


def _bool(description: str = "", required: bool = True,
          must_true: bool = None, must_false: bool = None,
          default_value: bool = False, origin: str = None,
          desc: str = "", **kwargs) -> type_def.Bool:
    """
    创建一个 bool 类型
    :param description:
    :param required:
    :param must_true
    :param must_false
    :param default_value
    :param desc
    :return:
    """
    description = desc or description

    if must_true is not None:
        condition = [True]
    elif must_false is not None:
        condition = [False]
    else:
        condition = None

    return type_def.Bool(
        default_value, required, description, origin=origin,
        validator=validator_constructor(choose_condition=condition), **kwargs
    )


def _string(description: str = "", required: bool = True,
            min_length: int = None, max_length: int = None,
            default_value: typing.Any = None, origin: str = None,
            desc: str = "", **kwargs) -> type_def.String:
    """
    创建一个字符串类型
    :param default_value:
    :param description:
    :param required:
    :param min_length:
    :param max_length:
    :param desc
    :return:
    """
    description = desc or description

    if min_length is not None and max_length is not None:
        validator = StringValidate(min_length=min_length, max_length=max_length)
    else:
        validator = None

    return type_def.String(
        default_value, required, description, origin=origin,
        validator=validator, **kwargs
    )


def _list(elem_type: typing.Union[RpcType, Model], description: str = "",
          required: bool = True, min_items: int = None, max_items: int = None,
          origin: str = None, desc: str = "", **kwargs) -> type_def.List:
    """
    创建一个列表类型
    :param elem_type:
    :param description:
    :param required:
    :param min_items
    :param max_items
    :param desc
    :return:
    """
    description = desc or description

    # 如果是 Model, 则转换为 Dict
    if getattr(elem_type, "__model_tag__", "") == "MT":
        elem_type: typing.Any = elem_type
        elem_type: type_def.Dict = copy.deepcopy(elem_type.get_fields())  # fs 即 dict 类型
        for v in elem_type.get_elem_info().values():
            v.rm_column()

    return type_def.List(
        elem_type, required, description, origin=origin,
        validator=ListValidate(min_length=min_items, max_length=max_items), **kwargs
    )


def _dict(fs: typing.Dict[str, RpcType] = None, description: str = "",
          required: bool = True, model: Model = None, validate: bool = True,
          origin: str = None, desc: str = "", **kwargs) -> type_def.Dict:
    """
    创建一个列表类型
    :param fs:
    :param description:
    :param required:
    :param model:
    :param validate: 是否要检查其中的字段
    :return:
    """
    description = desc or description

    validator = validate and DictValidate() or None
    d = type_def.Dict(required, description, validator=validator, origin=origin, **kwargs)
    fs = fs or {}
    for key, value in fs.items():
        d.add_field(key, value)

    if model:
        for key, value in model.get_fields().get_elem_info().items():
            try:
                d.add_field(key, copy.deepcopy(value).rm_column())
            except Exception:
                pass
    return d


def _enum(fs: typing.Dict[str, RpcType] = None, description: str = "",
          required: bool = True, validate: bool = True, name: str = "", default_value=None,
          origin: str = None, desc: str = "", **kwargs) -> type_def.Enum:
    """
    创建一个枚举类型
    :param fs: 为枚举类型的元素， 所有元素都只能是同一种类型
    :param description:
    :param required:
    :param validate: 是否要检查其中的字段
    :param name: 枚举名称, 当需要生成枚举接口时，如果没有传递，则使用对应变量的名称,
                 两个名称至少要定义一个
    :param desc
    :return:
    """
    description = desc or description

    validate_items = [v.default_value for v in fs.values()]
    validator = validate and ChoiceValidate(1, *validate_items) or None
    e = type_def.Enum(name, default_value, required, description, validator=validator, origin=origin, **kwargs)
    fs = fs or {}
    for key, value in fs.items():
        e.add_item(key, value)

    return e


def _params(
        params: typing.Dict[str, f_fields.Raw] = None,
        in_place: str = "query") -> typing.Dict[str, typing.Any]:
    """
    该函数用于设置 query 字段说明，主要是对 flask doc 使用方式的一个补充,
    该补充接口, 不支持定义嵌套类型
    在 RPC 项目中不会使用该函数

    @ns.doc(params=common_base,params({
        "name": fields.String(required=True),
    }))
    def get(self):
        pass
    """
    # 最终还是以字典的方式存储, 便于统一 flask 及原有的解析方式
    d = {}
    if not params:
        return d

    for key, value in params.items():
        d[key] = convert_flask_type_to_dict(value, in_place)

    return d


def _nested(model: Model = None, description: str = "",
            required: bool = True, validate: bool = True,
            desc: str = ""):
    description = desc or description
    return _dict(model.get_fields().get_elem_info(), description, required, model, validate)


class Fields(object):
    """
    创建各种类型的简易入口
    """

    Integer = _integer
    Float = _float
    Double = _double
    Bool = _bool
    Boolean = _bool
    String = _string
    List = _list
    Dict = _dict
    Time = _time
    Date = _date
    DateTime = _datetime
    Enum = _enum

    Model = _model
    model = _model
    index = IndexInfo
    args = args
    resp = resp
    Void = type_def.Void
    params = _params

    Nested = _nested

    # datasource
    datasource = stm.DataSource
    arg_holder = stm.Args
    pipe = Pipe
    loop = Loop

    # db field
    BigInteger = db_extend.big_integer
    SmallInteger = db_extend.small_integer
    LargeBinary = db_extend.large_binary
    Char = db_extend.char
    Decimal = db_extend.decimal
    Binary = db_extend.binary
    Text = db_extend.text
    json = db_extend.json
    allow_addition = allow_addition


# global fields for define
fields = Fields
