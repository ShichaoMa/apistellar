# apistar注入机制详解
### 术语解释
#### 全局唯一
- Injector：注入逻辑执行器，控制整个注入流程的组件类。
- components: 注入使用的所有组件，可被注入的对象为初始对象和components resolve方法的返回值
- initial: 初始的注入对象名称及注入对象类型的映射。
- reverse_initial: 初始的注入对象类型及注入对象名称的映射。
- 注入对象名称: 每个注入对象都有一个唯一的名称，用来查找注入对象。

#### 每个请求唯一
- state: 每次请求开始时创建的字典，保存着注入对象名称及注入对象映射。
- seen_state: 保存所有已发现的注入对象名称的集合。
- steps: 每次请求需要执行的函数链，其在解析on_request, handler on_response on_error后方可得到，每个step为一个元组，包含以下内容：
  - func: 需要执行的函数
  - is_async: 该函数是否是异步的
  - kwargs: 执行该函数所需要的参数名称及注入名称的映射，后续会将注入名称映射成注入对象。通过关键字参数的形式记录以方便传入
  - consts: 执行该函数可能依赖其之后的函数提供相关描述信息，如：HeaderComponent.resolve方法返回Header类型的对象，需要为HeaderComponent提供注入时参数的名称，consts保存了注入名称和注入参数对象。
  - output_name: 若执行该函数，他的返回值名称，也就是注入对象名称。
  - set_return: 是否将其返回值作为一次Injector.run的返回值。

### 注入逻辑
#### ASGI调用开始，传入scope，返回一个asgi_callable，闭包了scope，来保证其每个请求全局唯一。

#### 随后初始化了state字典，获取了所有hook的on_request方法及路由对应的hander，发起了针对这些方法的注入解析、注入及调用。

#### injector内部，解析传入的funcs，获取steps，解析逻辑如下：
- 使用initial创建seen_state，用以收集接下来发现的所有注入对象名称。
- 调用resolve_function方法解析每个func，遍历其参数，通过其注释类型从reverse_initial中获取注入对象名字，并保存到kwargs中。
- 对于不存在于reverse_initial中的注释类型，则遍历所有components，判断component是否可以处理这种注释类型(resolve返回这种类型)，
如果可以的话，为这个参数生成注入对象名称，保存到kwargs。同时将其为作output_name递归传入resolove_function来解析符合条件的component resolve方法。
- seen_state在递归的过程中不断被传入的，也就说从注入开始只存在一个seen_state。resolve_function最开始的调用时output_name是没有值的，因此可以通过函数返回值注释类型来判断output_name是什么。
通过查找reverse_initial，找到注入对象名称即为output_name，如果找不到，则output_name=return_value。
- 对于参数注释类型，有一种特殊情况就是当参数注释类型是inspect.Parameter时，则证明该函数需要获取其上一个函数待解析的参数对象。通常是为了获取这个参数名称才使用这种写法。其参数名称和参数对象被保存在了const中。
- 在resolve_function执行过程中，steps会收集所需要的步骤，其中包括递归时resolve_function的返回steps，还有当前函数所对应的step，最终返回steps。
- 每个func对应的steps是相对独立的，将所有steps合在一起遍历，将kwargs中的注入对象名字通过state转换成注入对象。将const融入kwargs中一同传递给每一步中的func，执行func,并
将其返回值及其output_name保存到state中，将随着遍历的进行，所有steps全部完成。