import requests


url = "http://127.0.0.1:8000/test_upload"

resp = requests.post(url, data={"project": "pangu"}, files={"test": ("aaaa.zip", open("/Users/mashichao/Downloads/zgtj.zip", "rb"), "application/zip"),
                                                            "test1": ("bbbb.png", open("/Users/mashichao/Downloads/asyncio.png", "rb"), "image/png")})

print(resp.text)