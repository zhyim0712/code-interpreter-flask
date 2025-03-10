# Code Interpreter for Flask

### 使用
```bash
curl --location --request POST 'https://codeinterpreter:8000' \
--header 'Content-Type: application/json' \
--data {
  "code": "print('Hello, World!')",
  "files": ["https://file_url.docx"],
  "session": "会话id，用于存储本次请求的变量，下次对话可以直接使用",
  "config": {
    "AWS_ACCESS_KEY_ID": "",
    "AWS_SECRET_ACCESS_KEY": "",
    "AWS_S3_REGION_NAME": "",
    "AWS_S3_ENDPOINT_URL": "",
    "AWS_S3_BUCKET_NAME": "",
    "REDIS_LOCATION": "",
    "REDIS_PASSWORD": "",
  }
}
```
#### config说明
- 用户会问一些敏感信息，所以这些信息不能存储到代码中，需要通过config传递
- 代码执行过程中生成的文件存储到S3中，返回到客户端是文件的url
- Redis用来存储一些变量，在实践过程中，AI会重复使用之前的变量，如果不存储，之前的变量会丢失，导致报错变量未定义

### 本地部署
- 建议使用docker部署，可以解决部分安全问题
- 用户A产生的文件用户B也是可以访问到的，这一块暂时没解决
```shell
docker compose build
docker compose up
```

### 原始项目地址
[Local-Code-Interpreter](https://github.com/MrGreyfun/Local-Code-Interpreter)