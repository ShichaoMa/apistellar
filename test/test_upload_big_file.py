import requests


url = "http://127.0.0.1:8000/test_upload"

resp = requests.post(url, files={"test": open("/Users/mashichao/Downloads/zgtj.zip", "rb"),
                                 "test1": open("/Users/mashichao/Downloads/asyncio.png", "rb")})

print(resp.text)