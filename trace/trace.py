import json
import bson

SPLITTER: str = "[SPLITTER]"


class TraceInfoError(Exception):
    pass


class TraceInfo(object):
    """
    TODO: 用于实现 open tracing 相关的接口
    """
    def __init__(self, identifier: str, trace_id: str = "", span_id: str = "1", meta=None):
        """
        identifier 用于作为该 TraceInfo 的当前标识符，比如使用当前调用的服务名
        meta 用于记录自定义信息，比如调用时间，及调用的接口名称等等
        用于记录 RPC 的调用链信息
        trace_id 指当次调用过程的标识符，可通过该标识符得到整个链条的调用详情
        span_id 指当次调用在整个链条中的序号, 该序号由字符串组成，每个序号由 , 分割具体形式为:
        1,
          1,1
            1,1,1
            1,1,2
            1,1,3
          1,2
            1,2,1
            1,2,2
            1,2,3
        表示的意义为：
        在一个调用链中，1 服务调用了 11 及 12 两个服务，11 又调用了 111、112、113 三个服务,
        12 则调用了 121、122、123 三个服务，可得出
        1 依赖于 11、12
        11 依赖于 111、112、113
        12 依赖于 121、122、123

        :param identifier
        :param trace_id:
        :param span_id:
        :param meta
        """
        self.identifier = identifier or "UNKNOWN.UNKNOWN"
        self.trace_id = trace_id or str(bson.ObjectId())
        self.span_id = span_id
        self.next_id = -1
        self.meta = meta or {}

    def set_meta(self, key: str, value):
        """
        为 trace info 添加元数据
        :param key:
        :param value:
        :return:
        """
        self.meta[key] = value

    def increase_span(self):
        """
        递增记录调用次数的 next_id
        """
        self.next_id += 1

    def next_span(self) -> str:
        """
        生成下一级 span id
        :return:
        """
        return "%s,%s" % (self.span_id, self.next_id)

    @staticmethod
    def from_exists(prev: 'TraceInfo', new_identifier: str, step_in: bool = True):
        if step_in:
            prev.increase_span()
        t = TraceInfo(new_identifier, prev.trace_id, step_in and prev.next_span() or prev.span_id)
        return t

    def encode(self) -> str:
        return SPLITTER.join([
            self.identifier,
            self.trace_id,
            self.span_id,
            json.dumps(self.meta)
        ])

    @staticmethod
    def decode(ts: str) -> 'TraceInfo':
        segments = ts.split(SPLITTER)
        if len(segments) != 4:
            raise TraceInfoError(f"接收到的 TraceInfo 的格式不正确, 错误的格式为: {ts}")

        return TraceInfo(segments[0], segments[1], segments[2], json.loads(segments[3]))

    def __repr__(self):
        """
        """
        return f"TraceInfo: I({self.identifier}) S({self.span_id}) T({self.trace_id}) N({self.next_id})"


def __test_trace_id__():
    root = TraceInfo("root")
    assert(root.span_id == "1")

    rpc1 = TraceInfo.from_exists(root, "rpc1")
    assert rpc1.span_id == "1,1"
    assert rpc1.trace_id == root.trace_id

    rpc2 = TraceInfo.from_exists(root, "rpc2")
    assert rpc2.span_id == "1,2"
    assert rpc2.trace_id == root.trace_id
