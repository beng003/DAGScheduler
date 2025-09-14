import sys
import os
from pathlib import Path
import json
import yaml
root_path = str(Path(__file__).resolve().parent.parent)
sys.path.append(root_path)
from utils.yaml_util import read_yaml

def batch_delete_json_files():
    # 获取 JobConfig 目录的绝对路径
    job_config_dir = os.path.join(str(Path(__file__).resolve().parent.parent), 'JobConfig')
    
    # 遍历JobConfig目录及其子目录
    for root, dirs, files in os.walk(job_config_dir):
        for file in files:
            # 检查文件是否为json文件
            if file.endswith('.json'):
                # 构建完整的文件路径
                json_file_path = os.path.join(root, file)
                try:
                    # 删除文件
                    os.remove(json_file_path)
                except Exception as e:
                    print(f'删除文件 {json_file_path} 时出错: {e}')

def batch_convert_yaml_to_json():
    # 获取 JobConfig 目录的绝对路径
    job_config_dir = os.path.join(root_path, 'JobConfig')
    alice_config = read_yaml(f"{job_config_dir}/alice_sf.yaml")
    bob_config = read_yaml(f"{job_config_dir}/bob_sf.yaml")
    
    for root, dirs, files in os.walk(job_config_dir):
        for file in files:
            if file == 'alice_sf.yaml' or file == 'bob_sf.yaml':
                continue
            if file.endswith('.yaml'):
                input_file = os.path.join(root, file)
                file_name = file.split('.')[0]
                
                try:
                    with open(input_file, "r") as yaml_file:
                        data = yaml.safe_load(yaml_file)
                    
                    data["sf_cluster_desc"] = alice_config["sf_cluster_desc"]
                    json_str = json.dumps(json.dumps(data))
                    output_file = os.path.join(root, f'alice_{file_name}.json')
                    with open(output_file, "w", encoding="utf-8") as json_file:
                        json_file.write(f"{json_str}")
                    
                    data["sf_cluster_desc"] = bob_config["sf_cluster_desc"]
                    json_str = json.dumps(json.dumps(data))
                    output_file = os.path.join(root, f'bob_{file_name}.json')
                    with open(output_file, "w", encoding="utf-8") as json_file:
                        json_file.write(f"{json_str}")
                        
                except Exception as e:
                    print(f'转换文件 {input_file} 时出错: {e}')

if __name__ == '__main__':
    batch_delete_json_files()
    batch_convert_yaml_to_json()