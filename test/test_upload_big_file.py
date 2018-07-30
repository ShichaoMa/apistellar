import requests


headers = {"Cookie": "uid=fc19f383321a-54a9-9534-30e2-45f6863b; nginx_proxy_session=zM75p5Qg2ff3LzMbQYuDIw..|1532656681|MMcf4JsU232YG5muABVESIBsMk4.; session=55ad75f2a38b160e3794aea7549038b9bb17bbdcd6c698a7989c898f28deba0b1ff828e460d387e0394006c26ecad116; sso_usession=55ad75f2a38b160e3794aea7549038b9bb17bbdcd6c698a7989c898f28deba0b1ff828e460d387e0394006c26ecad116; osession=043e42c4b792125af98a4739a71233a65eb8da6d572e7a354805379b235ea6934a2dbb14c9c3cb8ca205e1f838d90d6b744c2da93fb49c41d310868ee7a540dc54adfe17b7672b36fea7f9e3dacc41b7d82372b1ae5d1a4b99c618e1b31008be3cd4f7855fd089bfbd3fa4446681d5577309c38fb83c2494971fc1153ef944973f85e8bc86945ea2fd22a7057ca62b6b8dc3f47a95e4e535ff97f6b1eba22c4b23c485e3405823681131266daba26e2f78cf85dca5bccc80f0c49b26176eacc36f0bf52bec8c0bb8e76ca84cd5368b413f8963970cdcefcefea171778719d0106df7c4508dd4cf12aed037b72c26dc12"}

#url = "http://test.research.yiducloud.cn/api/upl/s3/upload/big/file"
url = "http://127.0.0.1:8000/test_upload"
#
# resp = requests.post(url, headers=headers, params={"project": "pangu"}, files={"test": ("aaaa.zip", open("/Users/mashichao/Downloads/zgtj.zip", "rb"), "application/zip"),
#                                                             "test1": ("bbbb.png", open("/Users/mashichao/Downloads/asyncio.png", "rb"), "image/png"),
#                                                                              "test2": open("/Users/mashichao/Downloads/滋养细胞肿瘤.pdf", "rb")})

resp = requests.post(url, data={"project": "pangu"}, files={"test": open("/Users/mashichao/Downloads/滋养细胞肿瘤.pdf", "rb"), "test2": open("test_bool.py")})
print(resp.text)

