model作为数据模型，如何将其持久化到数据库等服务中一直是一件值得关注的事情。早期model提供了类属性注入功能，可以为其注入数据库链接对象，如：
```python
class File(AsyncType):
    mongo_manger = inject << MongoManger
    TABLE = "s3"
    DB = "uploader"
    ...
```
通过左移符号来注入数据库链接对象，实现对数据库的操作。注入操作是由对应的ModelFactory来发起的，所以在每次调用Factory时，都会注入一次。如：
```python
class FileFactory(ModelFactory):
    model = File # 这里指定了要实施注入的model
    async def product(self, _id: http.QueryParam) -> File:
        return File(_id=_id)
```
这种解决方案会带来以下几个问题：
- 注入的发起严重依赖ModelFactory，如果model没有对应到一个ModelFactory，则注入无法完成
- 注入的对象在model中以类属性的方式存在，每次请求只要涉及到了ModelFactory的生产操作都会完成注入，也就是说请求之间会对model类属性的修改产生竞争条件。
- 对于绕过ModelFactory而直接使用model类的情况，model中可能不存在数据链接对象(若存在，由于类属性是全局唯一的，也仅仅是因为之前有请求使用过ModelFactory并完成过注入)，如果此时调用model中存在操作数据的方法，就会产生错误。

如果说前两个问题可以接受的话，那么第三个问题是无法容忍的，之前解决第三个问题的方案是，在服务启动之初手动完成一次注入，这样保证了每个model都是已注入过的状态，这样在直接使用model类时，至少可以保证不会出错。但是这种操作随之而来的是各种无法预料的服务不稳定。

所以基于以上情况，寻找一种优雅的持久化方案变的迫不急待。从apistellar==1.0.16起，通过实现DriverMixin的子类，并多继承其和PersistentType，来获取稳定的持久化能力。

该方案需要遵循以下标准：
- 继承DriverMixin，并实现其get_store方法，get_store方法用来获取存储驱动对象，并在其中提供资源回收释放等操作。
- 对于需要集成存储对象的类，多继承DriverMixin的子类，以获取存储能力。
- 对于需要使用存储对象的方法，使用conn_manager来装饰。
下面让我们举个栗子：

### 定义DriverMixin的子类
```python
from apistellar import DriverMixin, proxy, contextmanager
 
 
class SqliteDriverMixin(DriverMixin):
    INIT_SQL_FILE = "blog.sql"
    DB_PATH = "db/blog"
    store = None  # type: sqlite3.Cursor
    @classmethod
    @contextmanager
    def get_store(cls, self_or_cls, **callargs):
        with super(SqliteDriverMixin, cls).get_store(
            self_or_cls, **callargs) as self_or_cls:
            pool = ConnectionPool()
            try:
                # 获取连接
                conn = pool.get_conn()
                # 返回cur对象
                yield proxy(self_or_cls, prop_name="store", prop=conn.cursor())
            except Exception as e:
                # 异常回滚
                conn.rollback()
                raise e
            finally:
                # 提交操作
                conn.commit()
                # 释放
                pool.release(conn)

```
下面来让我们使用这个类，比如我们想在类A中的使用这个类，而类A继承于类B
```python
class A(B, SqliteDriverMixin):
    @conn_manager
    def get_data(self):
        self.store.execute("select .... ")
        ....

    @classmethod
    @conn_manager
    def load(cls):
        cls.store.execute("select .... ")
        ....
```
上述方法中的store，是conn.cursor()的返回值。每次调用上述方法，都会完成store的管理。

上面方法中的cls, self，并不是原来的类和实例，而是仅在locals作用域存在的唯一的代理对象， 其代理了store属性，所以不会出现不同方法不同实例之间的竞争条件，解决了上面提到的第二个问题。

对于Model的创建，通过继承PersistentType，可以让我们省掉 @conn_manager，如：
```python
class Article(PersistentType, SqliteDriverMixin):
    ....
    # 不需要conn_manager装饰器也可以提供上述功能
    async def load(self, **kwargs):
        ...
        self.store.execute(f"SELECT * FROM {self.TABLE} WHERE 1=1 {sub}", args)
        data = self.store.fetchone()
        ...
```
### 灵活的DriverMixin
DriverMixin在经过几次小迭代之后，已经变的相当灵活。其支持多继承，我们可以同时继承多个DriverMixin子类来获取多种服务的访问能力。多个DriverMixin协同工作时，会创建一个嵌套的proxy对象，通过上述的get_store的实现我们即可以看出这个效果。每个get_store都需要优先调用super()的get_store，这种调用方法保证了在多继承下所有get_store都会被执行，因此可以在层层代理之后获取所有被mixin的服务。
### 支持异步的DriverMixin
DriverMixin的异步能力要从以下两个方面来讲：
1. 业务类中方法是异步的，例如：

```python
class A(B, SqliteDriverMixin):
    @conn_manager
    async def find_one():
        ...
````
find_one即可以是同步的，也可以是异步的。

2. get_store被实现成异步
这种情况是由于我们可以需要在get_store通过异步的方式获取到要被mixin的服务，比如我们要创建一个mongo mixin， 但是mongo的地址是通过异步的方法获取的。这种情况下get_store只能被实现成一个异步生成器(python3.6+)
```python
class MongoDriverMixin(DriverMixin):
    @classmethod
    @contextmanager
    async def get_store(cls, self_or_cls, **callargs):
        addr = await get_addr()
        from motor.motor_asyncio import AsyncIOMotorClient
        yield AsyncIOMotorClient(addr)
        
```
这种情况是被允许，但是要注意：
  - contextmanager不再是python内置的，因为内置的不支持异步生成器。contextmanager要从apistellar从导入。
  - 异步Mixin最好不要被其它Mixin继承，除非你可以理清mro顺序。
  - 如果继承了异步Mixin创建业务类，那么其中的同步方法不能被conn_manager装饰。若装饰了，也不会有任何Mixin效果，还会收到警告。