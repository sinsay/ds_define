# ds_define
DataSource Definer - provide an easy way to describe your data model and api, update interface

## Usage

```python
# from ds_define import fields, CommonBase


# extend CommonBase mean's SomeApi will use to generate the code
# snip with definition
class SomeApi(CommonBase):
    @fields.args(fields.Model("SomeArgs", dict(
        arg1=fields.Integer(),
        arg2=fields.String(nullable=True)
    ))
    @fields.resp(fields.Dict(dict(
        field1=fields.String(),
        field2=fields.Dict(dict(
            names=fields.List(fields.String()),
            infos=fields.List(fields.Dict(dict(
                age=fields.Integer(),
                height=fields.Float()
            )))
        ))
    )))
    def hello(self):
        pass
```

the ds_gen project, can use this definition to gen some code like:
1. web service base on flask,
2. rpc server and client base on grpc
3. database define with orm sqlalchemy

all those generated code with strong type and validation, it can auto check the
args and the response's format, raise an error while the type or other limitation
didn't fit the definition.

the code generated like:

```python
class SomeApiHelloArgs(BaseType):
    def __init__(self, arg1: int = 0, arg2: typing.Union[str, None] = None):
        self.arg1 = age
        self.arg2 = arg2

    def to_dict(self) -> dict:
        # ....

    def from_dict(self, dict):
        # ...

    def to_rpc(self):
        # ...

    def from_rpc(self, rpc_arg: typing.Any):
        # ...

    # and so on


class SomeApiHelloResponse(BaseType):
    # ...


# web
class SomeApiResource(BaseResource):
    # ...


# rpc
class SomeApiRPC(RpcBase):
    # ...

```

and then, the code gen will generate some entrence to start the service, use it like:

```shell
python web_server,py
python rpc_server.py
```

use the generate rpc client like:

```python
from gen_path import SomeApi, SomeApiHelloArgs, SomeApiHelloResponse

# it will auto discover server by ds_runtime.config module
api = SomeApi()

arg: SomeApiHelloArgs = SomeApiHelloArgs(arg1 = 1)
resp: SomeApiHelloResponse = api.hello(arg)

print(resp)
```
