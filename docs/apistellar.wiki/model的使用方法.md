### model的定义
model通常被定义在模块根目录同名的文件中。

apistellar提供了两个Type基类以供继承，Type和PersistentType，PersistentType请看[model持久化方案](https://github.com/ShichaoMa/apistellar/wiki/model%E6%8C%81%E4%B9%85%E5%8C%96%E6%96%B9%E6%A1%88)。

model用来定义稳定的数据模型， 并包含一些验证，如
```python
class Book(Type):
    # 使用正则限制名称格式
    name = validators.String(pattern=r"<<.*?>>")
    # 枚举类型
    publisher = validators.String(enum=["新华出版社", "人民教育出版社", "人民邮电出版社"])
    # 作者最大长度不能超20
    author = validators.String(max_length=20)
    # 创建日期类型%Y-%m-%d 目前只支持这一种，可能自定义类型
    publish_date = validators.Date()
    # 不能小于100页
    page_num = validators.Integer(minimum=100)
    # float类型支持
    price = validators.Number(default=int)
    # 整除支持, 要2本2本买
    sale_per_count = validators.Integer(multiple_of=2)
    # 支持%Y-%m-%d %H:%M:%S
    created_at = validators.DateTime(default=datetime.datetime.now)
    # 是否在售
    on_sale = validators.Boolean(default=True)
    # 描述
    description = validators.String(allow_null=True)
```
### model对象创建
model对象可以通过以下方式创建
```python
# 原始json对象
book = {
        "page_num": 628,
        "price": 139.00,
        "sale_per_count": 2,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "on_sale": True,
        "description": None
        }
# 创建Book对象
book = Book(book)
 
book.name = "<<流畅的python>>"
book.publisher = "人民邮电出版社"
book.author = "Luciano Ramalho"
book.publish_date= "2017-5-15"
 
# 或者通过传入一个对象的形式创建
class A:
    def __init__(self):
        self.name = "<<流畅的python>>"
        self.publisher = "人民邮电出版社"
        self.author = "Luciano Ramalho"
a = A()
book = Book(a)
```
### 获取有效的的model
通过format() 方法可以校验对象中的字段有效性，通过`to_dict()` 方法可以将对象转换成字典。
```python

# 格式化b对象
book.format()
# 转换成字典
jsonobj = book.to_dict()
# 或者直接dump
json_str = json.dumps(book, cls=TypeEncoder())
```
### advance
更强大的用法如下
```python
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


class Employee(Type):
    name = Name
    # exclusive_maximum指定包含边界，即id <= 32
    id = validators.Integer(maximum=32, exclusive_maximum=True)
    # 当items是Employee时，Array中的对象全是Employee
    lovers = validators.Array(items=validators.Ref("Employee"))
    # 最多两项好爱好，第一项只能是唱片，第二项只能是Pad，不接受大于items长度的项
    hobbies = validators.Array(items=[Tape, Pad], additional_items=False)


employee = {"name": {"first_name": "Tom",
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

e = Employee(employee, force_format=True)
print(e.lovers[0].name.full_name)


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

```

### 使用Proxy代理一个model子类
validator支持使用一个Proxy类代理一个model子类。使用这种方式比直接在父类使用子类做为属性要优越许多，可以声明不同的代理对象来获取不同的子类实现效果。如：
```
class Subject(Type):
    id = validators.String(allow_null=True)
 
 
class Student(Type):
    name = validators.String()
    subject = validators.Proxy(Subject, allow_null=True)
 
 
class Teacher(Type):
    name = validators.String()
    subject = validators.Proxy(Subject, default=Subject)
```

### 自定义格式化类
有时我们可能需要复杂数据类型，设想我们需要一个tags字段，在使用一个json进行model初始化时，tags字段可以是这样的：git,python，通过,链接所有tags。但是我们希望在调用format后，我们的model中的tags可以通过model.tags得到["git", "python"]，同时，当我们将model序列化时，tags又能被连接成字符串。

通过继承apistellar.types.format:BaseFormat，我们可以定义Format类，下面我们定义一个TagsFormat来讲解他的用法。
```python
class TagsFormat(BaseFormat):

    type = list
    name = "tags"

    def is_native_type(self, value):
        return isinstance(value, self.type)

    def validate(self, value):
        if isinstance(value, str):
            return value.split(",")
        if isinstance(value, bytes):
            return value.decode().split(",")
        if isinstance(value, Sequence):
            return list(value)
        raise ValidationError('Must be a valid tags.')

    def to_string(self, value):
        if isinstance(value, str):
            value = value.split(",")
        return ",".join(value)

class Tags(validators.String):
    def __init__(self, **kwargs):
        super().__init__(format='tags', **kwargs)

```
通过以上代码，我们就创建一个Tags字段，并可以满足我们最初的需求。
