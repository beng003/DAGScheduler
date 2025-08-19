import yaml
import requests
from requests.exceptions import RequestException
import time
import os
import json
import pprint


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


data = load_yaml_data(
    "/disc/home/beng003/work/DAGScheduler/request/alice_request_data_ip4.yaml"
)
json_dict = json.loads(data["task_yaml"][0]["job_kwargs"])

# print(json_dict)
pprint.pprint(json_dict)

data["task_yaml"][0]["job_kwargs"] = json_dict

with open(
    "/disc/home/beng003/work/DAGScheduler/request/alice_request_data_ip444.yaml",
    "w",
    encoding="utf-8",
) as file:
    yaml.dump(data, file, default_flow_style=False, allow_unicode=True)


data = {
    "sf_cluster_desc": {
        "devices": {
            "spu_config": {
                "cluster_def": {
                    "nodes": [
                        {
                            "address": "192.168.0.10:9100",
                            "listen_address": "0.0.0.0:9100",
                            "party": "alice",
                        },
                        {
                            "address": "192.168.0.11:9100",
                            "listen_address": "0.0.0.0:9100",
                            "party": "bob",
                        },
                    ],
                    "runtime_config": {"field": 3, "protocol": 2},
                },
                "link_desc": {
                    "brpc_channel_connection_type": "pooled",
                    "brpc_channel_protocol": "http",
                    "connect_retry_interval_ms": 1000,
                    "connect_retry_times": 60,
                    "http_timeout_ms": 1200000,
                    "recv_timeout_ms": 1200000,
                },
            }
        },
        "sf_init": {
            "address": "192.168.0.10:6379",
            "cluster_config": {
                "parties": {
                    "alice": {
                        "address": "192.168.0.10:9200",
                        "listen_addr": "0.0.0.0:9200",
                    },
                    "bob": {
                        "address": "192.168.0.11:9200",
                        "listen_addr": "0.0.0.0:9200",
                    },
                },
                "self_party": "alice",
            },
        },
    },
    "sf_node_eval_param": {
        "input_path": {
            "alice": "/app/local_data/alice/alice.csv",
            "bob": "/app/local_data/bob/bob.csv",
        },
        "key": {"alice": ["id1"], "bob": ["id2"]},
        "output_path": {
            "alice": "/app/local_data/alice/psi-output.csv",
            "bob": "/app/local_data/bob/psi-output.csv",
        },
        "receiver": "alice",
    },
}
