# -*- coding: utf-8 -*-
import os
import base64
from .kernel import JupyterKernel, delete_color_control_char
from .client import S3Handler


def execute_python_code(
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
):
    old_files = []
    s3 = S3Handler(aws_ak, aws_sk, aws_region, aws_endpoint, aws_bucket)
    jupyter_kernel = JupyterKernel(session, redis_host, redis_password, redis_db)

    for file in files:
        s3.download_file(
            file.get("fileURL", None),
            jupyter_kernel.work_dir,
            file_name=file.get("fileName", None)
        )

    for root, dirs, _files in os.walk(jupyter_kernel.work_dir):
        old_files += _files

    content_to_display = jupyter_kernel.execute_code(code)
    jupyter_kernel.kernel_manager.shutdown_kernel()
    jupyter_kernel.kernel_client.shutdown()

    images, texts, files = [], [], []
    error = False
    for mark, out_str in content_to_display:
        if mark in ("stdout", "execute_result_plain", "display_plain"):
            texts.append(out_str)
        elif "png" in mark or "jpeg" in mark:
            if "png" in mark:
                images.append(("png", out_str))
            else:
                images.append(("jpg", out_str))
        elif mark == "error":
            texts.append(delete_color_control_char(out_str))
            error = True
    text = "\n".join(texts).strip("\n")

    # file output
    file_urls = []
    for root, dirs, files in os.walk(jupyter_kernel.work_dir):
        for file_name in files:
            if file_name in old_files:
                continue
            file_path = os.path.join(jupyter_kernel.work_dir, file_name)
            with open(file_path, "rb") as fp:
                url = s3.upload_file(
                    jupyter_kernel.session,
                    fp,
                    file_name=file_name,
                )
                file_urls.append(url)

    # image output
    img_urls = []
    for filetype, img in images:
        image_bytes = base64.b64decode(img)
        url = s3.upload_file(jupyter_kernel.session, image_bytes, suffix=filetype)
        img_urls.append(url)

    response = {
        "text": text,
        "images": img_urls,
        "files": file_urls,
        "error": error
    }

    return response
