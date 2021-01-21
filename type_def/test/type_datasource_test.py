from ...base import CommonBase
from ..type_util import fields
from ..datasource import args, func

# build model first
flow = fields.model("shfw_flow", dict(
    id=fields.Integer().column(primary_key=True),
    name=fields.String().column(),
    age=fields.Integer(maximum=100, minimum=0).column()
))

step = fields.model("shfw_step", dict(
    id=fields.Integer().column(primary_key=True),
    name=fields.String().column(),
    flow_id=fields.Integer().column(foreign="shfw_flow.id")
))

flow_info = fields.model("shfw_flow_info", dict(
    id=fields.Integer().column(primary_key=True),
    flow_id=fields.Integer().column(foreign="shfw_flow.id"),
    height=fields.Float().column(),
    weigh=fields.Float().column()
))


def __test_allow__():
    ds = fields.datasource()
    select = ds.select(flow.id)
    join = select.join(flow.id == flow_info.flow_id)
    filter_ = join.filter(flow.id == 1)
    _paging = filter_.skip(0).take(10)

    # chaining
    ds = fields.datasource()
    _result = ds.select(flow.id) \
        .join(flow.id == flow_info.flow_id) \
        .filter(flow.name.like('%SinSay%')) \
        .skip(10) \
        .take(10)


def __test_build_datasource__():
    ds = fields.datasource()
    select = ds.select(flow, flow_info.height, flow_info.weight)
    # auto join when compare between different model
    filter_ = select.filter(
        flow.id == flow_info.flow_id & flow_info.height > 170) \
        .quote() \
        .or_(flow.name != 'Hello')
    _paging = filter_.skip(1).take(20)

    sql_info = ds.sql_info()
    __build_sql__(sql_info)


def __build_sql__(_sql):
    pass


def __test_relation_get__():
    """
    测试将关联数据填充到自定义类型中
    :return:
    """
    _api_arg = fields.args(fields.model("args", dict(
        flow_id=fields.Integer()
    )))

    _api_resp = fields.resp(
        fields.model("resp", dict(
            flow=fields.datasource().select(flow).filter(flow.id == args.flow_id).first(),
            steps=fields.datasource().select(flow_info).filter(
                flow_info.flow_id == args.flow_id).take(10)
        ))
    )

    # should gen
    # flow = SELECT * from shfw_flow WHERE shfw_flow.id = :? LIMIT 1
    # steps = SELECT * FROM shfw_step WHERE shfw_step.flow_id = :? LIMIT 10


def __test_relation_join__():
    """
    测试将关联数据填充到自定义类型中
    :return:
    """
    _api_arg = fields.args(fields.model("args", dict(
        flow_id=fields.Integer()
    )))

    _flow_resp = fields.resp(
        fields.Dict(dict(
            flow_and_step_list=fields.datasource().select(flow, step.name.as_('step_name')).filter(
                flow.id == args.flow_id)
        ))
    )

    _step_resp = fields.resp(
        fields.Dict(dict(
            steps=fields.datasource().select(step, flow.name.as_("flow_name")).filter(
                step.flow_id == args.flow_id).skip(args.page * args.size).take(args.size)
        ))
    )


def __test_relation_save__():
    """
    测试从自定义数据中保存关联数据
    :return:
    """
    _api_arg = fields.args(fields.model("args", dict(
        flow=flow.exclude_primary(),
        steps=fields.List(step.exclude_primary())
    )))

    _resp_op = fields.resp(
        ok=fields.pipe(
            fields.datasource()
            .save(flow.exclude_primary())
            .values(flow.exclude_primary().as_args())
            .result(flow.id),
            # result=None the pipe's processor's result will be the result inject to next step's args
            result_as="flow_id"
        ).next(
            fields.loop(args.steps, item="step", index="i", skip=1) \
            .it(
                fields.datasource().save(step.exclude_primary())
                .values(
                    step.exclude(step.id),
                    step.flow_id.eq(args.flow_id)
                )
            )
            .collect()  # collect all loop result
        )
    )


def __test_book_library__():
    borrow_state = fields.Enum(dict(
        Steady=fields.Bool(default_value=True),
        Borrowed=fields.Bool(default_value=False)
    ), name="BorrowState")

    category = fields.model("category", dict(
        id=fields.Integer().column(primary_key=True),
        name=fields.String().column(length=11)
    ), description="书籍分类")

    book = fields.model("book", dict(
        id=fields.Integer().column(primary_key=True),
        name=fields.String().column(),
        cate=fields.Integer().column(foreign="category.id")
    ), description="书籍列表")

    book_set = fields.model("book_set", dict(
        id=fields.Integer().column(primary_key=True),
        book=fields.Integer().column(primary_key=True),
        sn=fields.String().column(length=11),
        borrowed=borrow_state.column()
    ), description="书籍分册, 每本书可能有多本")

    record = fields.model("record", dict(
        id=fields.Integer().column(primary_key=True),
        user=fields.Integer().column(),
        book=fields.Integer().column(foreign="book_set.id"),
        book_date=fields.DateTime().column(),
        send_back=fields.Bool().column()
    ), description="借书记录")

    class Book(CommonBase):

        @fields.resp(fields.Dict(dict(
            data=fields.datasource().select(category)
        )))
        def all_category(self):
            """
            获取所有书籍分类
            """
            pass

        @fields.args(fields.model("GetArgs", dict(
            name=fields.String(),
            page=fields.Integer(default_value=1),
            size=fields.Integer(default_value=10)
        )))
        @fields.resp(fields.Dict(dict(
            books=fields.datasource().select(
                book,
                fields.datasource().select(book_set.id.count())
                .filter(
                    book.id.eq(book_set.book) & book_set.borrowed.eq(
                        borrow_state.borrowed)
                ).alias("remain")
            ).filter(book.name.like(args.name)).paging(args.page, args.size)
        )))
        def book_list(self):
            """
            列出书籍列表，根据参数可以获取已借出或未借出的书
            :return:
            """
            pass

        @fields.args(fields.model("MyBookArgs", dict(
            user_id=fields.Integer(),
            send_back=fields.Bool(default_value=False)
        )))
        @fields.resp(fields.Dict(dict(
            books=fields.datasource().select(
                record,
                book.name.as_("book_name")
            ).filter(record.user.eq(args.user_id) & record.send_back.eq(args.send_back))
        )))
        def my_book(self):
            """
            列出我的借阅列表，根据参数可以显示已还或未还
            :return:
            """
            pass

        @fields.args(fields.model("BorrowBookArgs", dict(
            book_id=fields.Integer(),
            user_id=fields.Integer()
        )))
        @fields.resp(fields.Dict(dict(
            success=fields.pipe(
                # first choose the book set which still here
                fields.datasource().select(book_set.id).filter(
                    book_set.book.eq(
                        args.book_id) & book_set.borrowed.eq(False)
                ).first(),
                result_as="book_set_id"
            ).next(
                fields.datasource().update(
                    book_set.borrowed.eq(True)
                )
                .filter(book_set.id.eq(args.book_set_id))
                .next(
                    fields.datasource().save(record).values(
                        record.user.eq(args.user_id),
                        record.book.eq(args.book_set_id),
                        record.book_date.eq(func.now()),
                        record.send_back.eq(True)
                    )
                )
            )))
        )
        def borrow_book(self):
            """
            借阅一本书籍
            :return:
            """
            pass

        @fields.args(book.exclude_primary())
        @fields.resp(fields.Dict(dict(
            book_id=fields.pipe(
                fields.datasource().save(book.exclude_primary()).values(
                    book.exclude_primary().as_args())
                .result()
            )
        )))
        def new_book(self):
            """
            新增一本书籍
            """
            pass

    return Book
