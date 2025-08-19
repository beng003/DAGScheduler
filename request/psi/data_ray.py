import json
import yaml

def write_yaml(target, data):
    """
    将数据写入到指定的 YAML 文件中。

    参数:
    - target: 目标文件路径
    - data: 要写入的数据对象
    """
    with open(target, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)

# 读取YAML文件并转换为JSON字符串
def yaml_to_json_str(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            # 读取YAML文件内容
            yaml_content = yaml.safe_load(file)
            # print(type(yaml_content))
            # 将YAML内容转换为JSON字符串，确保中文正常显示
            json_str = json.dumps(yaml_content["param"], ensure_ascii=False)
            # with open('data.json', 'w', encoding='utf-8') as f:
            #     json.dump(json_str, f, ensure_ascii=False)
            return json_str
    except Exception as e:
        print(f"处理YAML文件时出错: {e}")
        return None

def data_generate(path:str):
    return {
        "task_uid": "job-alice-bob-040",
        "task_name": "task2",
        "task_initiator": "alice",
        "task_group": "default",
        "task_yaml": [
            {
                "job_uid": "psi3",
                "job_name": "psi3",
                "job_parties": "[\"party1\",\"party2\"]",
                "job_dependencies": "[]",
                "job_executor": "default",
                "invoke_target": "module_task.psi.psi_csv",
                "job_args": "",
                "job_kwargs": yaml_to_json_str(path)
            },
            {
                "job_uid": "psi4",
                "job_name": "psi2",
                "job_parties": "[\"party1\",\"party2\"]",
                "job_dependencies": "[\"psi3\"]",
                "job_executor": "default",
                "invoke_target": "module_task.scheduler_test.job",
                "job_args": "",
                "job_kwargs": ""
            }
        ],
        "concurrent": "1",
        "cron_expression": "0/10 * * * * ?",
        "misfire_policy": "3",
        "status": "1",
        "priority": "0",
        "remark": "test"
    }

path = "/disc/home/beng003/work/DAGScheduler/JobConfig/ray_psi_alice_ip4.yaml"
write_yaml("./request/alice_request_data_ip4.yaml",data_generate(path))


# # 主函数
# def main():
#     # 指定要读取的YAML文件路径
#     file_path = "/disc/home/beng003/work/DAGScheduler/JobConfig/ray_psi.yaml"
#     # 读取YAML文件并转换为JSON字符串
#     json_str = yaml_to_json_str(file_path)
    
#     print(f"读取文件: {file_path}")
#     print("文件内容(JSON格式):")
#     print(json_str)
#     # print(json.loads(json_str)['param'])


# # 执行主函数
# if __name__ == "__main__":
#     main()
