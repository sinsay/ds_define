from typing import List, Any, Union, Dict
from .type_def import RpcType, ArgSource


class Arg(object):
    def __init__(self, name: str, arg_type: RpcType, default, description: str = "",
                 required: bool = True, source: ArgSource = ArgSource.UNKNOWN):
        """
        参数描述，包括参数名及参数的类型及默认值
        :param name:
        :param arg_type:
        :param default:
        :param description:
        :param required:
        """
        self.name = name
        self.arg_type = arg_type
        self.default = default
        self.description = description or ""
        self.required = required
        self.source = source

        if self.arg_type.required is None:
            self.arg_type.required = self.required
        if self.arg_type.default_value is None:
            self.arg_type.default_value = self.default
        if self.arg_type.description is None:
            self.arg_type.description = self.description


class Entry(object):
    def __init__(self, name: str, args: List[Arg], result: Union[RpcType, None], description: str = ""):
        """
        表示一个 RPC 服务的入口, 保存了 RPC 所在的类型、函数、参数及返回值信息
        :param name: 该入口的名称
        :param args: 该入口所需的参数信息
        :param result: 该入口的返回值信息
        :param description: 该入口的注释信息
        """
        self.name = name
        self.args = args
        # map of type, result
        self._result = {}
        if result:
            self._result[200] = result

        self.description = description or ""

    @property
    def result(self):
        """
        获取当前 Entry 正常返回时的结果
        """
        return self._result.get(200)

    def get_results(self) -> Dict[int, RpcType]:
        """
        获取当前 Entry 的所有返回值
        """
        return self._result

    def gen_invalid_args(self):
        """
        生成错误的参数列表
        """
        args = []
        for arg in self.args:
            args.append(arg.arg_type.validator.gen_invalid())

        return args

    def get_result(self, result_type=200) -> Union[RpcType, None]:
        """
        获取指定类型的 Result
        """
        return self._result.get(result_type, None)

    def set_result(self, result_type: int, result: RpcType):
        self._result[result_type] = result

    def gen_invalid_args_dict(self) -> Any:
        """
        生成错误的参数信息，以字典的形式返回
        """
        args = {}
        for arg in self.args:
            args[arg.name] = arg.arg_type.validator.gen_invalid()

        return args

    def gen_invalid_result(self) -> Any:
        """
        生成错误的返回值信息，具体的格式由返回值定义的类型决定，如返回值为 int， 则返回一个数值，
        如返回值为 list 则返回一个列表
        """
        return self.result.validator.gen_invalid()


class MetaData(object):
    """
    描述 RPC 服务的元数据信息, 元数据主要包括以下信息
    1. 服务的总信息, 包括原始服务所在的包及类型
    2. 服务的入口信息，一个服务会有一个或多个入口
    3. 每个入口的参数及返回结果信息
    """
    def __init__(self, name,
                 # package,
                 service_type, entries: List[Entry] = None,
                 description: str = "", impl_type=None):
        """
        表示一个整体的 RPC 服务， name 为该服务的入口名称, service_type 是他原本的服务类型，
        entries 是该服务的入口列表, description 则为该服务的整体说明
        :param name:
        :param service_type:
        :param impl_type
        :param entries:
        :param description:
        """
        self.name: str = name
        # self.package = package
        self.service_type = service_type
        self.impl_type = impl_type
        self.entries: List[Entry] = entries or []
        self.description: str = description or ""

    def add_entry(self, entry: Entry):
        self.entries.append(entry)
