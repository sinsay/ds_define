import typing

from .ds_field import FieldOrAny
from .ds_base import DataSource


class Loop(object):
    """
    允许在数据模型定义中描述简易的循环操作, example:
    TODO: 支持 Range 等动态定义

    ```python
    from type_def import args, Loop, datasource

    table = SomeTable()

    Loop([1, 2, 3], index="index").it(datasource().save(table).value(table.field.eq(args.index))
    ```
    """

    def __init__(self, loop_elem: FieldOrAny,
                 item: typing.Union[str, None] = None,
                 index: typing.Union[str, None] = None,
                 skip: int = 1
                 ):
        """
        创建一个 Loop 循环

        :param loop_elem: 需要循环的元素, 可以来自与 args 或是 python 的可迭代类型
        :param item: 当前循环元素的名称，可以在循环中使用 args 获取
        :param index: 当前循环元素的索引名称，可以在循环中使用 args 获取
        :param skip: 每次循环需要跳过的元素个数，默认为 1， 即遍历所有元素
        """
        self._loop_elem = loop_elem
        self._item = item
        self._index = index
        self._skip = skip
        self._op = []

    def it(self, datasource: DataSource) -> 'Loop':
        self._op.append(datasource)
        return self
