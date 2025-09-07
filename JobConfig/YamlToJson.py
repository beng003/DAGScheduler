import sys
from pathlib import Path
root_path = str(Path(__file__).resolve().parent.parent)
sys.path.append(root_path)

from utils.yaml_util import convert_yaml_to_json_str

if __name__ == '__main__':
    input_file = 'JobConfig/sgbv/predict/ray_sgv_alice_ip4.yaml'
    output_file = 'JobConfig/sgbv/predict/ray_sgv_alice_ip4_str.json'
    convert_yaml_to_json_str(input_file, output_file)
    print(f'YAML 文件 {input_file} 已转换为 JSON 字符串并保存到 {output_file}')
    
    input_file = 'JobConfig/sgbv/predict/ray_sgv_bob_ip4.yaml'
    output_file = 'JobConfig/sgbv/predict/ray_sgv_bob_ip4_str.json'
    convert_yaml_to_json_str(input_file, output_file)
    print(f'YAML 文件 {input_file} 已转换为 JSON 字符串并保存到 {output_file}')
