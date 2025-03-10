# -*- coding: utf-8 -*-
import os
import uuid
from flask import Flask, request
from flask_cors import CORS
from src.execute import execute_python_code

app = Flask(__name__)
app.config["SECRET_KEY"] = "-vb@-em4+)*%0lh$o)zxn2dus-9&%o(#n2svsmxb004*cg@w%-"

CORS(
    app,
    resources=r"/*",
    origins=["*"],
    supports_credentials=True,
)


@app.route("/execute/", methods=["POST"])
def main():
    content = request.json
    code = content.get("code")
    files = content.get("files", [])
    config = content.get("config", {})
    aws_ak = config.get("AWS_ACCESS_KEY_ID")
    aws_sk = config.get("AWS_SECRET_ACCESS_KEY")
    aws_region = config.get("AWS_S3_REGION_NAME")
    aws_endpoint = config.get("AWS_S3_ENDPOINT_URL")
    aws_bucket = config.get("AWS_S3_BUCKET_NAME")
    redis_host = config.get("REDIS_LOCATION", "redis")
    redis_password = config.get("REDIS_PASSWORD", None)
    redis_db = config.get("REDIS_DB", 0)

    session = request.headers.get("session") or str(uuid.uuid4())
    # 创建缓存路径
    os.makedirs("/tmp/cache", exist_ok=True)

    response = execute_python_code(
        code,
        session,
        files,
        aws_ak,
        aws_sk,
        aws_region,
        aws_endpoint,
        aws_bucket,
        redis_host,
        redis_password,
        redis_db,
    )
    return response


if __name__ == "__main__":
    app.run(port=8000, debug=True)
