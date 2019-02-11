你可以很方便的使用websocket。
<br>
你可以像使用普通http action一样创建一个websocket action，如：
```python
@websocket("/test/websocket")
async def receive(message, path: Path):
    _text = message.get("text")

    print("received", _text, f"from {path}")
    return {"success": "ok"}
```
返回值将直接发送给客户端。让我们来测试一下，使用js创建一个websocket对象。并发送消息
````js
var ws = new WebSocket("ws://127.0.0.1:8000/test/websocket"); 
ws.send("hello,")
ws.send("world!")
ws.close()
````
服务端会打印如下信息：
```
DEBUG:websocket:Websocket of /test/websocket connect.
DEBUG:websockets.protocol:server << Frame(fin=True, opcode=1, data=b'hello,')
received hello, from /test/websocket
DEBUG:websockets.protocol:server >> Frame(fin=True, opcode=1, data=b'{"success": "ok"}')
DEBUG:websockets.protocol:server << Frame(fin=True, opcode=1, data=b'world!')
received world! from /test/websocket
DEBUG:websockets.protocol:server >> Frame(fin=True, opcode=1, data=b'{"success": "ok"}')
DEBUG:websockets.protocol:server << Frame(fin=True, opcode=8, data=b'')
DEBUG:websockets.protocol:server >> Frame(fin=True, opcode=8, data=b'')
DEBUG:websocket:Websocket of /test/websocket disconnect.
```
对于简单的收发消息，可使用这种方式。当然，我们也可以使用以下方法自定义websocket连接的建立和关闭的回调, 并且可以随时随地手动调用send方法从服务端主动向客户端发送消息：
```python
@websocket("/test/websocket1")
class Handler(object):
    def __init__(self, send):
        self.send = send
        self.message = ""

    async def websocket_connect(self, message, path: Path):
        print(f"Websocket of {path} connect. ")
        return {"success": "ok"}

    async def websocket_disconnect(self, message, path: Path):
        print("Got total data: %s" % self.message)
        print(f"Websocket of {path} disconnect. ")

    async def websocket_receive(self, message):
        text = message.get("text")
        self.message += text
        await self.send(f"got piece: {text}")
        await asyncio.sleep(1)
        return {"success": "ok"}
```
使用以上方法处理websocket连接，方法名是固定的。下面我们使用js创建一个websocket对象。并发送消息：
```js
var ws = new WebSocket("ws://127.0.0.1:8000/test/websocket1");
ws.onmessage = function (evt) {  // 收到服务器发送的消息后执行的回调
   console.log(evt.data);  // 接收的消息内容在事件参数evt的data属性中
};
ws.send("hello,")
VM82:2 got piece: hello,
VM82:2 {"success": "ok"}
ws.send("world")
VM82:2 got piece: world
VM82:2 {"success": "ok"}
ws.close()
```
服务打印的消息如下：
```
Websocket of /test/websocket1 connect.
DEBUG:websockets.protocol:server << Frame(fin=True, opcode=1, data=b'hello,')
DEBUG:websockets.protocol:server >> Frame(fin=True, opcode=1, data=b'got piece: hello,')
DEBUG:websockets.protocol:server >> Frame(fin=True, opcode=1, data=b'{"success": "ok"}')
DEBUG:websockets.protocol:server << Frame(fin=True, opcode=1, data=b'world')
DEBUG:websockets.protocol:server >> Frame(fin=True, opcode=1, data=b'got piece: world')
DEBUG:websockets.protocol:server >> Frame(fin=True, opcode=1, data=b'{"success": "ok"}')
DEBUG:websockets.protocol:server << Frame(fin=True, opcode=8, data=b'')
DEBUG:websockets.protocol:server >> Frame(fin=True, opcode=8, data=b'')
Got total data: hello,world
Websocket of /test/websocket1 disconnect.
```
此外，websocket使用的action方法，可以完美结合apistar依赖注入特性。使编程变的更加简单。

参考资料 [ASGI协议](https://github.com/django/asgiref/blob/master/specs/www.rst)