import requests


headers = {"Cookie": "nginx_proxy_session=1rCuoaKs_imbLtops8At_g..|1532570704|ThAZPxzObUWdBF2-P0NT-IgY4qc."}

url = "http://msc5.dev.yiducloud.cn/s3/download_big_file"
#url = "http://127.0.0.1:8000/test_download"

resp = requests.get(url, headers=headers, params={"_id": "2cf34227-3980-410f-bd22-868fa489bfef"}, stream=True)

with open("a.zip", "wb") as f:
    for chunck in resp.iter_content(1024000):
        f.write(chunck)