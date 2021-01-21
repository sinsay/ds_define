from ...type_util import fields
from ..ds_stm import EntryDataSource as Datasource


def test_pipe():
    user = fields.Model("user", dict(
        id=fields.Integer().column(primary_key=True),
        name=fields.String().column()
    ))

    info = fields.Model("info", dict(
        id=fields.Integer().column(primary_key=True),
        uid=fields.Integer().column(),
        age=fields.Integer().column()
    ))

    op = Datasource() \
        .select(user, info.age) \
        .join(info.uid.eq(user.id)) \
        .filter(user.id == 1)

    _p = fields.pipe(op).next(op).next(op, op, logic=fields.pipe.Or)
