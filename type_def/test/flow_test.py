from ... import fields, CommonBase
from ..datasource import *

# base model
Base = fields.model("", dict(
    id=fields.Integer(desc="主键").column(primary=True),
    is_deleted=fields.SmallInteger(desc="是否已删除").column(),
    create_time=fields.DateTime().column()
))

Flow = fields.model("shfw_flow", dict(
    name=fields.String(desc="流程名称").column(unique=True),
    creator=fields.Integer(desc="创建人").column(),
    datasource=fields.Integer(
        desc="流程的数据源, 表示整个流程的各个步骤都可共享的数据源",
        default_value=-1,
        foreign="shfw_datasource_map.id"
    ).column(),
    processor=fields.Integer(
        desc="流程的参与人员，表示可以启动流程的人员",
        default_value=-1,
        foreign="shfw_processor_map.id"
    ).column(),
), desc="flow 流程表").extend_model(Base)

Step = fields.model("shfw_step", dict(
    name=fields.String(desc="步骤名称").column(unique=True),
    creator=fields.Integer(desc="创建人").column(),
    datasource=fields.Integer(
        desc="步骤的数据源",
        default_value=-1,
        foreign="shfw_datasource_map.id"
    ).column(),
    processor=fields.Integer(
        desc="步骤的参与人员",
        default_value=-1,
        foreign="shfw_processor_map.id"
    ).column(),
    step_type=fields.Enum("StepEnum")
), desc="step 步骤表").extend_model(Base)

Link = fields.model("shfw_link", dict(
    step=fields.Integer(desc="关联的步骤").column(),
    parent=fields.Integer(desc="当前节点的上一节点", default_value=-1).column(),
    flow=fields.Integer(desc="节点关联的流程").column(),
), desc="连接表，用于为 Step 建立流转过程").extend_model(Base)

FlowInstance = fields.model("shfw_flow_i", dict(
    flow=fields.Integer(desc="实例对应的流程").column(),
    customize=fields.Integer(desc="流程的个性化配置").column(),
    current=fields.Integer(desc="该实例的当前所在步骤", default_value=-1).column(),
    creator=fields.Integer(desc="创建该实例的用户").column()
), desc="流程的实例").extend_model(Base)

StepInstance = fields.model("shfw_step_i", dict(
    flow=fields.Integer(desc="实例对应的流程实例").column(),
    customize=fields.Integer(desc="步骤的个性化配置").column(),
    creator=fields.Integer(desc="创建该实例的用户").column()
), desc="步骤的实例").extend_model(Base)

Customize = fields.model("shfw_customize", dict(
    processor=fields.Integer(
        desc="个性化处理人员，对应为 ProcessorMap 的标识符"
    ).column(foreign="shfw_processor_map.id"),
    datasource=fields.Integer(
        desc="个性化数据源，对应为 DataSourceMap 的标识符"
    ).column(foreign="shfw_processor_map.id")
), desc="流程或步骤实例的个性化配置").extend_model(Base)

History = fields.model("shfw_history", dict(
    prev=fields.Integer(desc="历史的前一节点").column(),
    next=fields.Integer(desc="历史的下一节点").column(),
    flow=fields.Integer(desc="该历史所处的流程实例").column(),
    step=fields.Integer(desc="该历史所处的步骤").column(),
    creator=fields.Integer(desc="生成该历史的用户").column(),
    operator=fields.String(desc="产生该历史的操作，暂定为操作对应的 Flow API").column(),
    context=fields.String(desc="操作的元数据，暂定为操作对应 API 时传递的参数 JSON").column()
), desc="流程的执行历史").extend_model(Base)

ProcessorMap = fields.model("shfw_processor_map", dict(
), desc="参与人员信息关联表").extend_model(Base)

DataSourceMap = fields.model("shfw_datasource_map", dict(
), desc="数据源信息关联表").extend_model(Base)

# 流程参与人员信息, TODO: 第二版迭代时这里需要进行优化，优化成通用的权限开关模块
Processor = fields.model("shfw_processor", dict(
    map_id=fields.Integer(desc="关联表标识符").column(foreign="shfw_processor_map.id"),
    allow_user=fields.Integer(desc="允许参与的人员").column(),
    allow_role=fields.Integer(desc="允许参与的角色").column(),
    fobid_user=fields.Integer(desc="禁止参与的人员").column(),
    forbid_role=fields.Integer(desc="禁止参与的角色").column()
), desc="流程参与人员配置").extend_model(Base)

# datasource 表
DataSource = fields.model("shfw_datasource", dict(
    map_id=fields.Integer(desc="关联表标识符").column(foreign="shfw_datasource_map.id"),
    db=fields.String(desc="数据库").column(),
    collection=fields.String(desc="数据表").column(),
    condition=fields.Integer(
        desc="数据源的默认配置， 默认配置可以有多条， 第一版迭代暂不实现",
        default_value=-1
    ).column(),
)).extend_model(Base)

FlowData = fields.model("shfw_flowdata", dict(
    flow_id=fields.Integer(desc="关联的工作流程").column(),
    step_id=fields.Integer(desc="关联的步骤").column(),
    hist_id=fields.Integer(desc="所在历史节点").column(),
    source=fields.Integer(desc="关联的数据源").column(),
    data_id=fields.Integer(desc="关联的数据标识符").column()
), desc="工作流数据关联表").extend_model(Base)


class Args:
    def done(self) -> 'DataSourceAPI':
        return DataSourceAPI()

    def args(self) -> 'Args':
        return self


class Resp:
    def done(self) -> 'DataSourceAPI':
        return DataSourceAPI()


class DataSourceAPI:
    def args(self, a) -> Args:
        return Args()

    def resp(self) -> Resp:
        return Resp()


def datasource() -> DataSourceAPI:
    d = DataSourceAPI()
    return d


CreateResponse = fields.model("CreateResponse", dict(
    status=fields.Enum({
        "OK": fields.Integer()
    }),
    data=fields.List()
))

args = fields.model("args", dict(
    page=fields.Integer(),
    size=fields.Integer(),
    name=fields.String()
))

fields.datasource()

source = fields.datasource \
    .select(Flow.id, Flow.name) \
    .filter(Flow.id == fields.arg_holder.id)


class FlowApi(CommonBase):
    # @fields.args(Flow.exclude_primary())
    @fields.args(args)
    @fields.resp(
        fields
            .datasource()
    )
    def get(self):
        pass

    @fields.args(Flow.exclude_primary())
    @fields.resp(
        fields.datasource()
            .insert(Flow.exclude_primary())
            .values(Flow.exclude_primary().as_args())
            .result()
            .choose(Flow.id)
    )
    def post(self):
        pass
