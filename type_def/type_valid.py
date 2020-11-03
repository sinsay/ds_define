import random
import typing

from ..util.rand_str import rand_str
from .type_error import ValidationError
from .type_def import List as ListType, Dict as DictType
from .type_valid_base import Validate, VALID_TYPE, EmptyValidate

Number = typing.Union[int, float]


class GreaterValidate(Validate):
    """
    GreaterValidate Check the type should greater than configure value
    """
    default_error_messages = {
        VALID_TYPE.invalid: "must greater then {n}, but got {v}"
    }

    def __init__(self, greater: Number):
        super().__init__()
        self.n = greater
        self.elem_type = type(greater)

    def valid(self, v: Number):
        if v is None:
            self.fail(VALID_TYPE.invalid)

        if v <= self.n:
            self.fail(VALID_TYPE.invalid, n=self.n, v=v)

    def gen_invalid(self) -> any:
        gen = random.randint(self.n - random.randint(2, 3 + self.n % 10), self.n - 1)
        if self.elem_type is float:
            gen += random.random()

        return gen


class LessValidate(Validate):
    default_error_messages = {
        "invalid": "must less then {n}, but got {v}"
    }

    def __init__(self, less: Number):
        super().__init__()
        self.n = less
        self.elem_type = type(less)

    def valid(self, v: any):
        if v is None:
            self.fail(VALID_TYPE.null)

        if v >= self.n:
            self.fail(VALID_TYPE.invalid, m=self.n, v=v)

    def gen_invalid(self) -> any:
        gen = random.randint(self.n + 1, self.n + random.randint(1, (self.n * 10) % 100))
        if self.elem_type is float:
            gen += random.random()

        return gen


class RangeValidate(Validate):
    default_error_messages = {
        "invalid": "{v} is out of range [{min}, {max}]"
    }

    def __init__(self, minimum: Number, maximum: Number):
        """
        校验的值必须在 minimum 跟 maximum 之间
        """
        super().__init__()
        self.min = minimum
        self.max = maximum
        if isinstance(minimum, int):
            self.e_type = int
        else:
            self.e_type = float

    def valid(self, v: Number):
        if v < self.min or v > self.max:
            self.fail(VALID_TYPE.invalid, v=v, min=self.min, max=self.max)

    def gen_invalid(self) -> Number:
        r = random.randint(1, 2)
        if r == 1:
            # generate greater
            v = random.randint(self.max, self.max + random.randint(1, self.max % 100 + 2))
        else:
            # lesser
            v = random.randint(self.min - random.randint(2, 100), self.min - 2)

        return v + self.e_type(random.random())


class ChoiceValidate(Validate):
    default_error_messages = {
        "invalid": "{v} is not valid with choice condition: n = {n}, data = {data}"
    }

    def __init__(self, n: int = 1, *args):
        """
        校验的值必须存在 n 个存在于 args 中
        n 为 1 时，校验的元素是单个值
        n 大于 1 时，校验的元素是个列表
        """
        super().__init__()
        self.n = n
        self.data = list(args)

    def add_valid(self, v: any):
        self.data.append(v)

    def valid(self, v: any):
        if isinstance(v, list):
            if len(v) != self.n or len(set(v).intersection(set(self.data))) != self.n:
                self.fail(VALID_TYPE.invalid, v=v, data=self.data)
        elif v not in self.data:
            self.fail(VALID_TYPE.invalid, v=v, n=self.n, data=self.data)

    def gen_invalid_one(self):
        any_data = random.choice(self.data)
        if isinstance(any_data, str):
            return rand_str()
        elif isinstance(any_data, (int, float)):
            orig = sum(self.data) * random.random()
            while orig in self.data:
                orig = orig + random.randint(-10, 10)
            t = type(any_data)
            return t(orig)
        elif isinstance(any_data, bool):  # should with only one elem
            return not self.data[0]
        else:
            raise NotImplementedError("还未支持生成复杂对象的非法值")

    def gen_invalid_more(self):
        n = random.randint(max(self.n - 10, 1), self.n + 5)
        if self.n == n:
            return self.gen_invalid_more()

        return [self.gen_invalid_one() for _ in range(n)]

    def gen_invalid(self) -> any:
        if self.n == 1:
            return self.gen_invalid_one()
        else:
            return self.gen_invalid_more()


class StringValidate(Validate):
    default_error_messages = {
        "invalid": "{v} is not valid with choice condition: n = {n}, data = {data}"
    }

    def __init__(self, min_length: int = None, max_length: int = None):
        super(StringValidate, self).__init__()
        if min_length is None and max_length is None:
            raise ValidationError("Error: String 类型的检查器必须配置 min_length 或 max_length")

        self.min_length = min_length
        self.max_length = max_length

        if min_length is not None and max_length is None:
            validator = GreaterValidate(min_length)
        elif min_length is not None and max_length is not None:
            validator = RangeValidate(min_length, max_length)
        elif min_length is None and max_length is not None:
            validator = LessValidate(max_length)
        else:
            validator = None

        self.validator = validator

    def valid(self, v: str):
        if not self.validator:
            return

        if not v:
            self.fail(VALID_TYPE.null)

        self.validator.valid(len(v))

    def gen_invalid(self) -> str:
        if self.min_length is not None and self.max_length is None:
            # 如果只有最小值，则生成一个比最小值小的
            return rand_str(0, self.min_length - 1)
        elif self.min_length is not None and self.max_length is not None:
            # 如果是个区间，则生成大于最大值的
            return rand_str(self.max_length, self.max_length + 30)
        elif self.min_length is None and self.max_length is not None:
            # 如果只有最大值，则生成比最大值还要大的
            return rand_str(self.max_length, self.max_length + 30)
        else:
            return ""


class ListValidate(Validate):
    def __init__(self, min_length: int = None, max_length: int = None):
        super().__init__()
        self.validator = validator_constructor(min=min_length, max=max_length)

    def valid(self, v: typing.List[typing.Any]):
        if v is None:
            self.fail(VALID_TYPE.null)

        self.validator.valid(len(v))

        elem_type = self.host.get_elem()
        for idx, item in enumerate(v):
            try:
                if item is None and not elem_type.required:
                    continue
                elem_type.validator.valid(item)
            except ValidationError as exc:
                raise ValidationError({"@index[%s]" % idx: exc.msg})

    def gen_invalid(self) -> any:
        n = self.validator.gen_invalid() or 1
        elem_type = self.host.get_elem()
        invalid_data = []
        for _ in range(n):
            if elem_type:
                invalid_elem = elem_type.validator.gen_invalid()
            else:
                invalid_elem = None
            invalid_data.append(invalid_elem)

        return invalid_data

    def set_host(self, host: ListType):
        self.host = host


class DictValidate(Validate):
    def valid(self, v: typing.Dict[str, typing.Any]):
        """
        检查必须的字段是否存在
        """
        if v is None:
            self.fail("Error: Dict object can not be None")

        host = self.host
        _errors = dict()
        for key, value in host.get_elem_info().items():
            item_value = v.get(key, None)
            if item_value is None and not value.required:
                continue

            try:
                value.validator.valid(item_value)
            except ValidationError as exc:
                _errors[key] = exc.msg

        if _errors:
            raise ValidationError(_errors)

    def gen_invalid(self) -> any:
        """
        生成所需的字典对象，并随机缺失 n 个字段
        """
        n = random.randint(0, 3)
        invalid_data = {}
        host: DictType = self.host
        for key, value in host.get_elem_info().items():
            # 当还有需要欠缺的字段时
            if n % 2 == 1 and random.randint(0, 2) == 1:
                n -= 1
                continue

            invalid_data[key] = value.validator.gen_invalid()

        return invalid_data

    def set_host(self, host: DictType):
        self.host = host


class ValidCombiner(Validate):
    """
    组合验证器的基类，后续通过它为各种验证器的组合实现算法
    """

    def valid(self, v: any):
        raise ValidationError("Not Implement ValidCombiner")

    def gen_invalid(self) -> any:
        raise ValidationError("Not Implement ValidCombiner")


def validator_constructor(**kwargs):
    """
    通过判断参数中是否存在指定字段，来生成对应的 validator
    能够生成 validator 的参数名如下:
    min, max 能够组合生成 Greater、Less、Between Validator
    choose_n, choose_condition 用于生成 Choice
    """
    min_length = kwargs.pop("min", None)
    max_length = kwargs.pop("max", None)
    validator = []

    if min_length is None and max_length is not None:
        validator.append(LessValidate(max_length))
    elif min_length is not None and max_length is None:
        validator.append(GreaterValidate(min_length))
    elif min_length is not None and max_length is not None:
        validator.append(RangeValidate(min_length, max_length))

    choose_n = kwargs.pop("choose_n", None)
    choose_condition = kwargs.pop("choose_condition", None)
    if choose_condition:
        if choose_n is None:
            choose_n = 1

        validator.append(ChoiceValidate(choose_n, choose_condition))

    # TODO: 后续要支持多种 Validator 的组合
    return validator and validator[0] or EmptyValidate()
