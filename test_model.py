# -*- coding:utf-8 -*-
import json
import time
import datetime
from star_builder.types import Type, validators, TypeEncoder


class Book(Type):
    # 使用正则限制名称格式
    name = validators.String(pattern=r"<<.*?>>")
    # 枚举类型
    publisher = validators.String(enum=["新华出版社", "人民教育出版社", "人民邮电出版社"])
    # 作者最大长度不能超20
    author = validators.String(max_length=20)
    # 创建日期类型%Y-%m-%d 目前只支持这一种，可能自定义类型
    publish_date = validators.Date(default=datetime.datetime.now)
    # 不能小于100页
    page_num = validators.Integer(minimum=100)
    # float类型支持
    price = validators.Number()
    # 整除支持, 要2本2本买
    sale_per_count = validators.Integer(multiple_of=2)
    # 支持%Y-%m-%d %H:%M:%S
    created_at = validators.DateTime()
    # 是否在售
    on_sale = validators.Boolean()
    # 当allow_null=True时，若其值为None, 如果指定了default，会使用default
    description = validators.String(allow_null=True, default="这是一段描述")

# 原始json对象
book = {
        "page_num": 628,
        "price": 139.00,
        "sale_per_count": 2,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "on_sale": True,
        "description": None
        }
# 创建Book对象， 当指定Book(book, force_format=True)时，会强制校验数据合法性
b = Book(book)
# 赋值时会校验数据合法性
b.name = "13444" # 这条数据会报错

# 下面的数据不会报错
b.name = "<<流畅的python>>"
b.publisher = "人民邮电出版社"
b.author = "Luciano Ramalho"
b.publish_date = "2017-5-15"

# 直接dumps,需要指定cls=TypeEncoder, 同时会校验数据合法性
print(json.dumps(b, cls=TypeEncoder, indent=2))
# to_json返回json字典，同时会校验数据合法性，当to_json(force_format=False)时，数据合法性不会校验
print(b.to_json())


# model可以从对象中获取
class A:
    def __init__(self):
        self.name = "<<流畅的python>>"
        self.publisher = "人民邮电出版社"
        self.author = "Luciano Ramalho"
a = A()
t = Book(a)
print(json.dumps(t, cls=TypeEncoder))


class Name(Type):
    first_name = validators.String()
    last_name = validators.String()
    # 可以引用自身
    full_name = validators.Ref("Name", default="全名")

    # 当Name作为其它对象的属性时，可以允许是Null
    @classmethod
    def allow_null(cls):
        return True


class Tape(Type):
    hours = validators.Integer()
    name = validators.String()


class Pad(Type):
    wight = validators.Number()
    brand = validators.String()


class People(Type):
    name = Name
    # exclusive_maximum指定包含边界，即len(id) <= 32
    id = validators.Integer(maximum=32, exclusive_maximum=True)
    # 当items是People时，Array中的对象全是People
    lovers = validators.Array(items=validators.Ref("People"))
    # 最多两项好爱好，第一项只能是唱片，第二项只能是Pad，不接受大于items长度的项
    hobbies = validators.Array(items=[Tape, Pad], additional_items=False)


people = {"name": {"first_name": "Tom",
                     "last_name": "Cat",
                     "full_name": None},
            "id": 13,
            "lovers": [{"name": {
                "first_name": "Bill",
                "last_name": "Gate",
                "full_name": {"first_name": "bill", "last_name": "gate"}
            },
            "id": 1, "lovers": [], "hobbies": [{"hours": 2, "name": "my heart will go on "}]}],
            "hobbies": [{"hours": 3, "name": "audio"}, {"wight": 3, "brand": "apple"}]}

p = People(people, force_format=True)
print(p.lovers[0].name.full_name)


class Ipad(Pad):
    # 覆盖父类属性
    brand = validators.String(enum=["apple"])
    # 创建一个union对象，price可以是Number类型或String类型
    price = validators.Union([validators.Number(), validators.String()])


class Box(Type):
    ipads = validators.Array(items=Ipad)


box = {"ipads": [{"wight": 10.1,
        "brand": "apple",
        "price": 10.0}, {"wight": 10.1,
        "brand": "apple",
        "price": "拾圆整"}]}

b = Box(box, force_format=True)
print(b.ipads[1].price)


