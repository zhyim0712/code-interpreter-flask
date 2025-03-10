import jupyter_client
import re
from loguru import logger
import json

from .client import RedisClient


def delete_color_control_char(string):
    ansi_escape = re.compile(r"(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]")
    return ansi_escape.sub("", string)


def get_kernel_variables(kernel_client):
    # 请求当前内核中的全局变量，并将其序列化成 JSON 字符串
    code = """
    import json
    expect_keys = [
        'In',
        'Out',
        'expect_keys',
    ]
    def get_serializable_variables():
        variables = {}
        for k, v in globals().items():
            try:
                json.dumps(v)
                if k not in expect_keys and not k.startswith("_"):
                    variables[k] = v
            except (TypeError, OverflowError):
                pass
        return variables

    variables = get_serializable_variables()
    json_str = json.dumps(variables)
    print(json_str)
    """
    kernel_client.execute(code)
    json_str = None
    while True:
        msg = kernel_client.get_iopub_msg(timeout=2)
        content = msg["content"]
        msg_type = msg["msg_type"]
        if msg_type == "stream":
            if content.get("name") == "stdout":
                json_str = content["text"]
        if msg_type == "error":
            logger.error(delete_color_control_char("\n".join(content["traceback"])))
        elif msg_type == "status" and content.get("execution_state") == "idle":
            break
    return json_str


class JupyterKernel:
    def __init__(self, session, redis_host, redis_password, redis_db):
        self.rc = RedisClient(host=redis_host, password=redis_password, db=redis_db)
        self.session = session
        self.kernel_manager, self.kernel_client = (
            jupyter_client.manager.start_new_kernel(kernel_name="python3")
        )
        self.work_dir = f"/tmp/cache/{session}"
        self._create_work_dir()

    def _collect_output(self, msg_id):
        all_output = []
        while True:
            msg = self.kernel_client.get_iopub_msg()
            if msg["parent_header"].get("msg_id") == msg_id:
                content = msg["content"]
                msg_type = msg["msg_type"]
                if msg_type == "stream":
                    if content.get("name") == "stdout":
                        all_output.append(("stdout", content["text"]))
                elif msg_type == "execute_result":
                    for key in ("text/plain", "text/html", "image/png", "image/jpeg"):
                        if key in content["data"]:
                            all_output.append(
                                (
                                    f"execute_result_{key.split('/')[-1]}",
                                    content["data"][key],
                                )
                            )
                elif msg_type == "display_data":
                    for key in ("text/plain", "text/html", "image/png", "image/jpeg"):
                        if key in content["data"]:
                            all_output.append(
                                (f"display_{key.split('/')[-1]}", content["data"][key])
                            )
                elif msg_type == "error":
                    all_output.append(("error", "\n".join(content["traceback"])))
                elif msg_type == "status" and content.get("execution_state") == "idle":
                    break
        return all_output

    def _execute_code(self, code):
        msg_id = self.kernel_client.execute(code)
        all_output = self._collect_output(msg_id)
        return all_output

    def _load_variables(self, code):
        variables = self.rc.get_cache(self.session)
        code_with_variables = ""
        if variables:
            for key, value in json.loads(variables).items():
                if isinstance(value, str):
                    code_with_variables += f"{key} = '{value}'\n"
                else:
                    code_with_variables += f"{key} = {value}\n"
        return code_with_variables + code

    def execute_code(self, code):
        code = self._load_variables(code)
        content_to_display = self._execute_code(code)
        variables = get_kernel_variables(self.kernel_client)
        self.rc.create_cache(self.session, variables)

        return content_to_display

    def _create_work_dir(self):
        # set work dir in jupyter environment
        init_code = (
            f"import os\n"
            f"if not os.path.exists('{self.work_dir}'):\n"
            f"    os.mkdir('{self.work_dir}')\n"
            f"os.chdir('{self.work_dir}')\n"
            f"del os"
        )
        self._execute_code(init_code)
