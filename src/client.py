import os
import boto3
import requests
from time import time
from redis import StrictRedis
from redis.sentinel import Sentinel


class ClientException(Exception):
    pass


class S3Handler(object):
    def __init__(self, aws_ak, aws_sk, aws_region, aws_endpoint, aws_bucket):
        aws_region = aws_region
        aws_endpoint = aws_endpoint
        self.aws_bucket = aws_bucket
        self.BASE_URL = (
            f"https://{aws_bucket}.s3.{aws_region}.amazonaws.com.cn/{{}}"
        )

        session = boto3.Session(
            aws_access_key_id=aws_ak,
            aws_secret_access_key=aws_sk,
            region_name=aws_region,
        )
        self.client = session.client("s3", endpoint_url=aws_endpoint)

    def upload_file(self, session_id, file_bytes, file_name=None, suffix=None):
        if file_name is None:
            assert suffix, "Please input file type."
            file_name = f"{time()}.{suffix}"
        assert file_bytes, "File not found."
        key = f"{session_id}/{file_name}"

        self.client.put_object(
            Body=file_bytes,
            Key=key,
            Bucket=self.aws_bucket,
        )
        return self.BASE_URL.format(key)

    @staticmethod
    def download_file(url, save_path, file_name=None):
        if not url:
            return None
        if not file_name:
            assert "." in url.split("/")[-1], "您上传了一个非法的文件链接"

        response = requests.get(url)
        filename = file_name if file_name else url.split("/")[-1]
        with open(f"{save_path}/{filename}", "wb") as fp:
            fp.write(response.content)
        return f"{filename}"


class RedisClient(object):
    def __init__(self, host="redis", password=None, db=0):
        mode = os.environ.get("REDIS_MODE", "cluster")
        if mode == "standalone":
            self.redis = StrictRedis(
                host=host,
                port=6379,
                password=password,
                decode_responses=True,
                db=db,
            )
        else:
            sentinels = [(host, 26379)]
            sentinel = Sentinel(sentinels=sentinels, socket_timeout=0.1, sentinel_kwargs={"password": password})
            self.redis = sentinel.master_for(service_name="mymaster", socket_timeout=0.1, password=password, db=db)

    def get_cache(self, key, default_value=None):
        return self.redis.get(key) or default_value

    def create_cache(self, key, value):
        self.redis.set(key, value, ex=15 * 24 * 3600)

    def remove_cache(self, key):
        return self.redis.delete(key)

