import json
import yaml

__all__ = ["json_to_yaml", "read_yaml", "write_yaml", "convert_yaml_to_json_str"]


def json_to_yaml(json_file_path, yaml_file_path):
    """
    将 JSON 文件内容转换为 YAML 格式，并保存到指定的 YAML 文件中。

    :param json_file_path: JSON 文件的路径
    :param yaml_file_path: 保存 YAML 文件的路径
    """
    try:
        # 读取 JSON 文件
        with open(json_file_path, "r", encoding="utf-8") as json_file:
            json_data = json.load(json_file)

        # 将 JSON 转换为 YAML
        yaml_data = yaml.dump(
            json_data, default_flow_style=False, sort_keys=False, allow_unicode=True
        )

        # 将 YAML 写入到指定文件
        with open(yaml_file_path, "w", encoding="utf-8") as yaml_file:
            yaml_file.write(yaml_data)

        print(f"YAML 文件已保存到 {yaml_file_path}")

    except Exception as e:
        print(f"Error: {e}")


def convert_yaml_to_json_str(input_file, output_file):
    # 直接加载YAML文件并解析
    with open(input_file, "r") as yaml_file:
        data = yaml.safe_load(yaml_file)

    # sf_cluster_desc_alice = {
    #     "devices": {
    #         "spu_config": {
    #             "cluster_def": {
    #                 "nodes": [
    #                     {
    #                         "address": "192.168.0.10:9100",
    #                         "listen_address": "0.0.0.0:9100",
    #                         "party": "alice",
    #                     },
    #                     {
    #                         "address": "192.168.0.11:9100",
    #                         "listen_address": "0.0.0.0:9100",
    #                         "party": "bob",
    #                     },
    #                 ],
    #                 "runtime_config": {"field": 3, "protocol": 2},
    #             },
    #             "link_desc": {
    #                 "brpc_channel_connection_type": "pooled",
    #                 "brpc_channel_protocol": "http",
    #                 "connect_retry_interval_ms": 1000,
    #                 "connect_retry_times": 60,
    #                 "http_timeout_ms": 1200000,
    #                 "recv_timeout_ms": 1200000,
    #             },
    #         },
    #         "heu_config": {
    #             "evaluators": [{"party": "alice"}],
    #             "he_parameters": {
    #                 "key_pair": {"generate": {"bit_size": 2048}},
    #                 "schema": "ou",
    #             },
    #             "mode": "PHEU",
    #             "sk_keeper": {"party": "bob"},
    #         },
    #     },
    #     "sf_init": {
    #         "address": "192.168.0.10:6379",
    #         "cluster_config": {
    #             "parties": {
    #                 "alice": {
    #                     "address": "192.168.0.10:9200",
    #                     "listen_addr": "0.0.0.0:9200",
    #                 },
    #                 "bob": {
    #                     "address": "192.168.0.11:9200",
    #                     "listen_addr": "0.0.0.0:9200",
    #                 },
    #             },
    #             "self_party": "alice",
    #         },
    #     },
    # }

    # data["sf_cluster_desc"] = sf_cluster_desc_alice
    
    # 转换为紧凑的单行JSON字符串，保持所有转义字符
    json_str = json.dumps(json.dumps(data))
    # 写入文件（保持原始转义格式）
    with open(output_file, "w", encoding="utf-8") as json_file:
        json_file.write(f"{json_str}")


def read_yaml(target):
    # if isinstance(target, str) or isinstance(target, bytes):
    #     return yaml.load(target, Loader=yaml.FullLoader)
    with open(target, encoding="utf-8") as f:
        return yaml.load(f.read(), Loader=yaml.FullLoader)


def write_yaml(target, data):
    """
    将数据写入到指定的 YAML 文件中。

    参数:
    - target: 目标文件路径
    - data: 要写入的数据对象
    """
    with open(target, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)
