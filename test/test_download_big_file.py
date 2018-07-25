import requests

url = "http://127.0.0.1:8000/test_download"

resp = requests.get(url, params={"filename": "/Users/mashichao/Downloads/zgtj.zip"}, stream=True)

with open("a.zip", "wb") as f:
    for chunck in resp.iter_content(1024000):
        f.write(chunck)