# -*- coding:utf-8 -*-
from star_builder import Type, validators
import uuid
import datetime



class GroupFillingRate(Type):
    """队列填充率"""
    group_id = validators.String()
    enum_list = validators.Array(items=validators.String())
    total_value_count = validators.Integer(minimum=0)
    valid_value_count = validators.Integer(minimum=0)
    invalid_value_count = validators.Integer(minimum=0)
    value = validators.Number()


class FillingRate(Type):
    """填充率"""
    update_time = validators.DateTime(allow_null=True)
    total_value_count = validators.Integer(minimum=0, default=0)
    valid_value_count = validators.Integer(minimum=0, default=0)
    invalid_value_count = validators.Integer(minimum=0, default=0)
    value = validators.Number(default=0)
    enum_list = validators.Array(items=validators.String(), default=list)
    group = validators.Array(items=GroupFillingRate, default=list)

    @classmethod
    def has_default(cls):
        return True


class Variable(Type):
    """统计变量"""
    _id = validators.String(format="UUID", default=uuid.uuid4)
    desease_id = validators.String(default="")
    project_id = validators.String(default="")
    name = validators.String(default="")
    parent_project_key = validators.String(default="")  # 父级project_key
    project_key = validators.String(default="")  # project_key
    row_index = validators.Integer(minimum=0, allow_null=True)  # 组自增题行index
    follow_group_id = validators.String(default="")  # 随访队列id
    follow_stage_id = validators.String(default="")  # 随访阶段id
    follow_round = validators.Integer(minimum=0, allow_null=True)  # 随访点
    follow_parent_ques_id = validators.String(default="")  # 随访父级题目id
    follow_ques_id = validators.String(default="")  # 随访题目id
    is_group_variable = validators.Boolean(default=False)  # 是否是组别变量
    order = validators.Integer(minimum=0, default=0)  # 排序
    create_time = validators.DateTime(default=datetime.datetime.now)
    filling_rate = FillingRate  # 填充率

a = Variable({})
a.format()
import pdb;pdb.set_trace()
print(a)
b = a.to_json()
c = Variable(b)
c.format()
print(c)
d = c.to_json()
e = Variable(d)
e.format()
print(e)
# import json
# b = json.dumps({'phase_name': 'basic_name'})
# print(json.loads(b.))

