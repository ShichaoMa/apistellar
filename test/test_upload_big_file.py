import requests


headers = {"Cookie": "nginx_proxy_session=1rCuoaKs_imbLtops8At_g..|1532570704|ThAZPxzObUWdBF2-P0NT-IgY4qc."}

#url = "http://msc5.dev.yiducloud.cn/s3/upload_big_file"
url = "http://127.0.0.1:8000/test_upload"

resp = requests.post(url, headers=headers, data={"project": "pangu"}, files={"test": ("aaaa.zip", open("/Users/mashichao/Downloads/zgtj.zip", "rb"), "application/zip"),
                                                            "test1": ("bbbb.png", open("/Users/mashichao/Downloads/asyncio.png", "rb"), "image/png")})

print(resp.text)