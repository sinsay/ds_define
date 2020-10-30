"""
    该包主要是为 rpc 公共库提供一个通用的类型注解机制
    提供的函数会尽量贴近原有 flask 接口，便于旧接口的升级
"""

import copy
import typing
import datetime

from flask_restplus import fields as f_fields

from . import db_extend
from .type_base import ColumnInfo, IndexInfo
from .type_def import Integer as TInt, Bool as TBool, String as TStr, Float as TFloat, \
    Double as TDouble, Date as TDate, DateTime as TDateTime, Time as TTime, \
    List as TList, Dict as TDict, Void, RpcType, Enum as TEnum
from .type_valid import validator_constructor, StringValidate, DictValidate, ListValidate, \
    ChoiceValidate

MYSQL = 'MYSQL'
SUPPORT_INDEX_TYPES = {
    MYSQL: ['hash', 'btree']
}


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
        User = fields.model("she_user", {
            "id": fields.Integer(description="xxx").column(primary_key=True, index=True),
            "name": fields.String().column(length=32),
            "other": fields.Float().column()
        },
        description="user table",
        indexes=[fields.index('ind_id_name', columns=['id', 'name'], index_type=fields.index.HASH)])
        or
        User.add_indexes([fields.index(columns=['id', 'other'])])
        """
        d = _dict(fs, description)
        self.name = name
        self.fs = d
        self.indexes = []
        if indexes:
            self.add_indexes(indexes)

        # 用来标识该 model 是参数还是返回值后
        self.type = None

    def extend(self, field_name: str, field_type: RpcType):
        """
        扩展 model，在当前 Model 的基础上构建一个新的 Model，
        并为其增加 类型为 field_type 的字段 field_name
        """
        m2 = copy.deepcopy(self)
        m2.fs.add_field(field_name, field_type)
        return m2

    def extend_model(self, model: 'Model', rm_column_info: bool = True):
        """
        扩展 model, 在当前 Model 的基础上构建一个新的 Model,
        并将参数 m 中的字段信息复制到新的 Model 中
        """
        # 被用来扩展的 Model 会被移除 ORM 信息，防止解析到重复的表定义
        m2 = copy.deepcopy(self)
        for k, v in model.fs.get_elem_info().items():
            v = copy.deepcopy(v)
            if rm_column_info:
                v.rm_column()

            m2.fs.add_field(k, v)

        return m2

    def extend_to_db_model(self, model: 'Model'):
        m2 = copy.deepcopy(self)
        for k, v in model.fs.get_elem_info().items():
            m2.fs.add_field(k, copy.deepcopy(v))

        return m2

    def get_columns(self) -> typing.List[ColumnInfo]:
        """
        获取该模型的数据库字段定义
        """
        cols = []
        for name, field in self.fs.get_elem_info().items():
            if not field.is_column():
                continue
            col: ColumnInfo = field.get_column()
            col.set_name(name)
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
                raise Exception(f'index must has one column or more')
            if index.index_type not in SUPPORT_INDEX_TYPES[db_type]:
                raise Exception(
                    f'{db_type} not support index type :{index.index_type}, please choice ({",".join(SUPPORT_INDEX_TYPES[db_type])})) ')
            for index_column in index.columns:
                if index_column not in set([col.name for col in cols]):
                    raise Exception(f'the column:{index_column} not defined in this table:{self.name}')

    def _aggr_indexes(self, old_indexes: typing.List[IndexInfo] = None, new_indexes: typing.List[IndexInfo] = None):
        """如果本身model有indexes,则后者覆盖前者,以 columns列表为主;
        如果本身 column 有字段 index=True,以 column 定义为主,避免重复定义
        """
        old_indexes_c = copy.deepcopy(old_indexes) or []
        new_indexes_column = [new_index.columns for new_index in new_indexes]
        cur_indexes = new_indexes + [old_index for old_index in old_indexes_c if
                                     old_index.columns not in new_indexes_column]
        column_indexes_name = [[col.name] for col in self.get_columns() if col.index == True]
        return [cur_index for cur_index in cur_indexes if cur_index.columns not in column_indexes_name]

    def add_indexes(self, indexes: typing.List[IndexInfo] = None):
        """为表额外添加索引,可添加复合索引,可设置索引的类型"""
        if not self.fs._column_info:
            raise Exception("is not column dont add indexs")
        indexes = indexes or []
        self._check_index(indexes)
        self.indexes = self._aggr_indexes(self.indexes, indexes)


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


rpc_doc_args_key = "_rpc_doc_args"
rpc_doc_type_key = "_rpc_doc_type"
rpc_doc_resp_key = "_rpc_doc_resp"


def wrap(t: str, m: typing.Union[Model, RpcType]):
    # 只有 result type 会是 RpcType，因为只有 result 才能够不具有名称
    if isinstance(m, RpcType) and t == "args":
        raise Exception("参数定义必须有名称，args 不能与 RpcType 同时使用.")

    if isinstance(m, Model):
        m = m.fs

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
             default_value: int = None, origin: str = None) -> TInt:
    """
    创建一个 integer 类型
    :param description:
    :param required:
    :param minimum
    :param maximum
    :param default_value
    :return:
    """
    return TInt(
        default_value, required, description, origin=origin,
        validator=validator_constructor(min=minimum, max=maximum)
    )


def _float(description: str = "", required: bool = True,
           minimum: float = None, maximum: float = None,
           default_value: float = None, origin: str = None) -> TFloat:
    """
    创建一个浮点数类型
    :param description:
    :param required:
    :param minimum
    :param maximum
    :param default_value
    :return:
    """
    return TFloat(
        default_value, required, description, origin=origin,
        validator=validator_constructor(min=minimum, max=maximum)
    )


def _double(description: str = "", required: bool = True,
            minimum: float = None, maximum: float = None,
            default_value: float = None, origin: str = None) -> TDouble:
    """
    创建一个 Double 类型
    :param description:
    :param required:
    :param minimum
    :param maximum
    :param default_value
    :return:
    """
    return TDouble(
        default_value, required, description, origin=origin,
        validator=validator_constructor(min=minimum, max=maximum)
    )


def _time(description: str = "", required: bool = True,
          minimum: float = None, maximum: float = None,
          in_format: str = None, out_format: str = None,
          default_value: datetime.time = None, origin: str = None) -> TTime:
    """
    创建一个 Time 类型, WARN: 该类型只能表示时间戳
    :param description:
    :param required:
    :param minimum
    :param maximum
    :param default_value
    :return:
    """
    return TTime(
        default_value, required, description, origin=origin,
        in_format=in_format, out_format=out_format,
        validator=validator_constructor(min=minimum, max=maximum)
    )


def _date(description: str = "", required: bool = True,
          minimum: float = None, maximum: float = None,
          in_format: str = None, out_format: str = None,
          default_value: datetime.date = None, origin: str = None) -> TDate:
    """
    创建一个 Date 类型, WARN: 该类型只能表示时间戳
    :param description:
    :param required:
    :param minimum
    :param maximum
    :param default_value
    :return:
    """
    return TDate(
        default_value, required, description,
        in_format=in_format, out_format=out_format, origin=origin,
        validator=validator_constructor(min=minimum, max=maximum)
    )


def _datetime(description: str = "", required: bool = True,
              minimum: float = None, maximum: float = None,
              in_format: str = None, out_format: str = None,
              default_value: datetime.datetime = None, origin: str = None) -> TDateTime:
    """
    创建一个 DateTime 类型, WARN: 该类型只能表示时间戳
    :param description:
    :param required:
    :param minimum
    :param maximum
    :param default_value
    :return:
    """
    return TDateTime(
        default_value, required, description,
        in_format=in_format, out_format=out_format, origin=origin,
        validator=validator_constructor(min=minimum, max=maximum)
    )


def _bool(description: str = "", required: bool = True,
          must_true: bool = None, must_false: bool = None,
          default_value: bool = False, origin: str = None) -> TBool:
    """
    创建一个 bool 类型
    :param description:
    :param required:
    :param must_true
    :param must_false
    :param default_value
    :return:
    """
    if must_true is not None:
        condition = [True]
    elif must_false is not None:
        condition = [False]
    else:
        condition = None

    return TBool(
        default_value, required, description, origin=origin,
        validator=validator_constructor(choose_condition=condition)
    )


def _string(description: str = "", required: bool = True,
            min_length: int = None, max_length: int = None,
            default_value=None, origin: str = None) -> TStr:
    """
    创建一个字符串类型
    :param default_value:
    :param description:
    :param required:
    :param min_length:
    :param max_length:
    :return:
    """

    if min_length is not None and max_length is not None:
        validator = StringValidate(min_length=min_length, max_length=max_length)
    else:
        validator = None

    return TStr(
        default_value, required, description, origin=origin,
        validator=validator
    )


def _list(elem_type: typing.Union[RpcType, Model], description: str = "", required: bool = True,
          min_items: int = None, max_items: int = None, origin: str = None) -> TList:
    """
    创建一个列表类型
    :param elem_type:
    :param description:
    :param required:
    :param min_items
    :param max_items
    :return:
    """
    # 如果是 Model, 则转换为 Dict
    if getattr(elem_type, "__model_tag__", "") == "MT":
        elem_type: typing.Any = elem_type
        elem_type: TDict = copy.deepcopy(elem_type.fs)  # fs 即 dict 类型
        for v in elem_type.get_elem_info().values():
            v.rm_column()

    return TList(
        elem_type, required, description, origin=origin,
        validator=ListValidate(min_length=min_items, max_length=max_items),
    )


def _dict(fs: typing.Dict[str, RpcType] = None, description: str = "",
          required: bool = True, model: Model = None, validate: bool = True, origin: str = None) -> TDict:
    """
    创建一个列表类型
    :param fs:
    :param description:
    :param required:
    :param model:
    :param validate: 是否要检查其中的字段
    :return:
    """
    validator = validate and DictValidate() or None
    d = TDict(required, description, validator=validator, origin=origin)
    fs = fs or {}
    for key, value in fs.items():
        d.add_field(key, value)

    if model:
        for key, value in model.fs.get_elem_info().items():
            try:
                d.add_field(key, copy.deepcopy(value).rm_column())
            except:
                pass
    return d


def _enum(fs: typing.Dict[str, RpcType] = None, description: str = "",
          required: bool = True, validate: bool = True, name: str = "", default_value=None,
          origin: str = None) -> TEnum:
    """
    创建一个枚举类型
    :param fs: 为枚举类型的元素， 所有元素都只能是同一种类型
    :param description:
    :param required:
    :param validate: 是否要检查其中的字段
    :param name: 枚举名称, 当需要生成枚举接口时，如果没有传递，则使用对应变量的名称,
                 两个名称至少要定义一个
    :return:
    """
    validate_items = [v.default_value for v in fs.values()]
    validator = validate and ChoiceValidate(1, *validate_items) or None
    e = TEnum(name, default_value, required, description, validator=validator, origin=origin)
    fs = fs or {}
    for key, value in fs.items():
        e.add_item(key, value)

    return e


def _void(**_kwargs) -> Void:
    return Void()


_basic_fields = [
    "required", "default_value", "default", "description",
    "max_items", "min_items", "maximum", "minimum",
    "min", "max"
]

_flask_field_mapping: typing.Dict[typing.Any, typing.Any] = {
    f_fields.Boolean: bool,
    f_fields.Integer: int,
    f_fields.Float: float,
    f_fields.String: str,
}


def _convert_flask_type_to_dict(field: f_fields.Raw, place: str) -> typing.Dict[str, typing.Dict]:
    d = {}
    for key in _basic_fields:
        value = getattr(field, key, None)
        if value is None:
            continue
        d[key] = value

    t = _flask_field_mapping.get(type(field), None)
    if t is None:
        raise TypeError(f"flask restplus doc 的 params 定义不支持类型: {field}")

    d["type"] = t
    d["in"] = place
    return d


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
        d[key] = _convert_flask_type_to_dict(value, in_place)

    return d


def _nested(model: Model = None, description: str = "",
            required: bool = True, validate: bool = True):
    return _dict(model.fs.get_elem_info(), description, required, model, validate)


def allow_addition():
    def w(cls):
        # doc 只加在原始的函数上
        while hasattr(cls, "__wrapped__"):
            cls = cls.__wrapped__
        setattr(cls, "allow_addition", True)
        return cls

    return w


_index = IndexInfo


class Fields(object):
    """
    创建各种类型的简易入口

    Integer: 创建一个整数类型
    Float:   创建一个浮点数类型
    Double:  创建一个 Double 类型
    Bool:    创建一个布尔类型
    String:  创建一个字符串类型
    List:    创建一个列表类型
    Dict:    创建一个字典类型
    args:    创建一个服务的参数描述
    resp:    创建一个服务的返回值描述
    """

    def __init__(self):
        self.Integer = _integer
        self.Float = _float
        self.Double = _double
        self.Bool = _bool
        self.Boolean = _bool
        self.String = _string
        self.List = _list
        self.Dict = _dict
        self.Time = _time
        self.Date = _date
        self.DateTime = _datetime
        self.Enum = _enum

        self.model = _model
        self.index = _index
        self.args = args
        self.resp = resp
        self.Void = _void
        self.params = _params

        self.Nested = _nested

        # db field
        self.BigInteger = db_extend.big_integer
        self.SmallInteger = db_extend.small_integer
        self.LargeBinary = db_extend.large_binary
        self.Char = db_extend.char
        self.Decimal = db_extend.decimal
        self.Binary = db_extend.binary
        self.Text = db_extend.text
        self.json = db_extend.json
        self.allow_addition = allow_addition


def is_builtin_type(obj) -> bool:
    """
    检查 obj 是否基础类型
    """
    return isinstance(obj, (int, str, float, bool)) or obj is None


fields = Fields()


def __test__():
    other_model = fields.model('transfer_model', {
        "avatar_url": fields.String(
            description="用户头像",
            min_length=12, max_length=33),
        "company_name": fields.String(description="公司名称"),
        "id": fields.Integer(description="用户ID", minimum=20),
        "age": fields.Float(description="age", maximum=99),
        "mobile": fields.String(description="用户电话", min_length=9, max_length=9),
        "real_name": fields.String(description="真是姓名")
    })

    m = fields.model("response", {
        "status": fields.Integer(
            description="接口返回状态"),
        "msg": fields.String(description="接口返回描述信息"),
        "data": fields.Dict(model=fields.model("list_transfer", {
            "list": fields.List(
                fields.Dict(
                    model=other_model,
                ),
                min_items=10,
                description="评价列表",
            )
        }, description="用户历史交易列表"))
    })

    invalid_data = m.fs.validator.gen_invalid()
    if invalid_data.get("data", {"list": []}).get("list", None):
        invalid_data["data"]["list"] = invalid_data["data"]["list"] * 2

    import json
    print(json.dumps(invalid_data, indent=4))
    try:
        m.fs.validator.valid(invalid_data)
    except Exception as e:
        print(f"must occur exception here: {str(e)}")
        raise e
    return m


def __test_db__():
    user_table = fields.model("User", {
        "id": fields.Integer().column(primary_key=True, index=True),
        "name": fields.String().column(nullable=False, length=30),
        "age": fields.SmallInteger().column(nullable=True)
    }, description="数据库的 User 表")

    print(user_table.get_columns())

    tweet_table = fields.model("Tweet", {
        "id": fields.Integer().column(primary_key=True),
        "title": fields.String().column(length=255),
        "user_id": fields.Integer().column(foreign="User.id"),
    }, description="User 发表的 Tweet")

    print(tweet_table.get_columns())


def __test_enum__():
    status_enum = fields.Enum({
        "OK": fields.Integer(default_value=200),
        "FAIL": fields.Integer(default_value=500),
    },
        default_value=200,
        description="测试枚举类型")

    assert status_enum.default_value == 200
    status_enum.validator.valid(200)
    try:
        status_enum.validator.valid(300)
    except Exception as e:
        print(f"error '{str(e)}' should happen always")

    try:
        error_enum = fields.Enum({
            "GET": fields.Integer(default_value=200),
            "POST": fields.String(default_value="POST")
        })
        error_enum.get_type()
    except Exception as e:
        print(f"enum with difference type should raise Exception {str(e)}")
