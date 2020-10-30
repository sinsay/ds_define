"""
该模块定义了与 Flask RestPlus 类似的接口，用于支持框架同时生成 RPC 及 Web 服务
"""

import typing

from ..type_def import RpcType
from ..base import CommonBase


class Namespace(object):
    """
    命名空间，用于将多个服务添加到同一个子域名中
    """
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    def add_resource(
            self,
            resource: typing.Union[typing.Type[CommonBase], str],
            *urls,
            params: typing.Dict[str, RpcType] = None):
        """
        添加一个 Resource 类到指定的命名空间中，这里的 resource 不是 Flask 的 Resource,
        而是指继承了 CommonBase 的类型
        当 resource 得到的是 str 类型时，说明 namespace 被当成了装饰器使用，将返回一个 NamespaceDecorator
        params 则用于在 url 包含命名参数时，为参数增加描述信息
        """
        if isinstance(resource, str):
            return NamespaceDecorator(self, resource, *urls, params=params)
        elif issubclass(resource, CommonBase):
            inject_namespace(self.name, self.description, resource, urls, params=params)
            return resource
        else:
            raise TypeError(
                "Wrong type with namespace, the first argument for Namespace must be one of CommonBase or str instance")


class NamespaceDecorator(object):
    """
    命名空间装饰器，用于将命名空间信息添加到类型中
    """
    def __init__(self, ns: Namespace, *urls, params: typing.Dict[str, RpcType] = None):
        self.urls = urls
        self.ns = ns
        self.params = params

    def __call__(self, cls: typing.Type[CommonBase]):
        # inject namespace info to cls
        inject_namespace(self.ns.name, self.ns.description, cls, *self.urls, params=self.params)
        return cls


class NamespaceInfo(object):
    """
    TODO: 调整存储的信息，支持一个 Resource 对应多个 Url
    """
    def __init__(self, name: str = None, description: str = None, *urls, params: typing.Dict[str, RpcType] = None):
        self.name = name
        self.description = description
        self.urls = urls or []
        self.params = params or {}


def inject_namespace(
        name: str, description: str,
        resource: typing.Type[CommonBase],
        *urls,
        params: typing.Dict[str, RpcType] = None):
    """
    注入命名空间信息到 cls 中
    """
    ns_info = getattr(resource, "__ns_info__", None)
    if ns_info is None:
        ns_info = NamespaceInfo()

    ns_info.name = name
    ns_info.description = description
    ns_info.urls.extend(urls)
    ns_info.params.update(params or {})

    setattr(resource, "__ns_info__", ns_info)


def get_namespace(cls) -> typing.Union[None, NamespaceInfo]:
    return getattr(cls, "__ns_info__", None)


def __use_case__():
    from ..type_def import fields

    ns = Namespace("login")
    ns.add_resource(CommonBase, "/login")

    ns.add_resource(CommonBase, "/login_with_id/<int:id>", params={
        "id": fields.Integer()
    })

    @ns.add_resource("/login/<int:user_id>", params={
        "user_id": fields.Integer()
    })
    class Hello(CommonBase):
        def get(self):
            pass

    # 为了消除警告而调用
    Hello()
