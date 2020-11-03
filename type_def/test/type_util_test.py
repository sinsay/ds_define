from src.common.type_def.type_util import *


def __test_build_mode_and_validate__():
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


def __test_build_db__():
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


def __test_build_enum__():
    status_enum = fields.Enum({
        "OK": fields.Integer(default_value=200),
        "FAIL": fields.Integer(default_value=500),
    },
        default_value=200,
        description="测试枚举类型"
    )

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
