import yaml
import requests
from requests.exceptions import RequestException
import time
import os

def load_yaml_data(file_path):
    """从YAML文件中加载数据"""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"错误：文件 {file_path} 未找到")
        return None
    except yaml.YAMLError as e:
        print(f"YAML解析错误: {e}")
        return None


def send_request(
    json_data,
    method="POST",
    url="http://bob_dag_scheduler.h100.secretflow.icu:8000/scheduler",
    headers={},
    params={},
):
    """根据YAML中的数据发送HTTP请求"""
    try:
        print(f"正在发送 {method} 请求到 {url}")

        response = requests.request(
            method=method, url=url, headers=headers, params=params, json=json_data
        )

        print(f"响应状态码: {response.status_code}")
        print("响应内容:")
        print(response.text)

        return response

    except KeyError as e:
        print(f"配置错误: 缺少必要的键 {e}")
        return None
    except RequestException as e:
        print(f"请求发送失败: {e}")
        return None

def add_and_exec(party:str):
    terminal_width = os.get_terminal_size().columns
    print("="*terminal_width)
    # YAML文件路径
    yaml_file = f"./request/{party}_request_data_ip4.yaml"
    
    if party == "alice_local":
        party = "alice"

    # 加载YAML数据
    data = load_yaml_data(yaml_file)
    if not data:
        return

    # 发送请求
    response = send_request(
        json_data=data,
        method="POST",
        url=f"http://{party}_dag_scheduler.h100.secretflow.icu:8000/scheduler/task/add",
        headers={},
        params={},
    )
    
    # time.sleep(1)

    # 这里可以添加对响应的处理逻辑
    if response:
        print(f"{party}任务添加成功")
        
    task_uid = response.json()["task_uid"]

    # 发送请求
    response = send_request(
        json_data=data,
        method="POST",
        url=f"http://{party}_dag_scheduler.h100.secretflow.icu:8000/scheduler/task/start",
        headers={},
        params={"task_uid":task_uid},
    )
    
     # 这里可以添加对响应的处理逻辑
    if response:
        print(f"{party}任务开始执行")
        
    print("="*terminal_width)


def main():
    add_and_exec("alice")
    # time.sleep(1)
    add_and_exec("bob")
    # add_and_exec("alice_local")

if __name__ == "__main__":
    main()
