from utils.common_util import SnakeCaseUtil
import json
import yaml


# 读取YAML文件并转换为JSON字符串
def yaml_to_json_str(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            # 读取YAML文件内容
            yaml_content = yaml.safe_load(file)
            # 将YAML内容转换为JSON字符串，确保中文正常显示
            json_str = json.dumps(yaml_content, ensure_ascii=False)
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(json_str, f, ensure_ascii=False)
            return json_str
    except Exception as e:
        print(f"处理YAML文件时出错: {e}")
        return None


# 主函数
def main():
    # 指定要读取的YAML文件路径
    file_path = "/disc/home/beng003/work/DAGScheduler/JobConfig/ray_psi.yaml"
    # 读取YAML文件并转换为JSON字符串
    json_str = yaml_to_json_str(file_path)
    
    print(f"读取文件: {file_path}")
    print("文件内容(JSON格式):")
    print(json_str)


# 执行主函数
if __name__ == "__main__":
    main()


# a["taskYaml"] = SnakeCaseUtil.transform_result(a["taskYaml"])
# print(json.dumps(SnakeCaseUtil.transform_result(a)))
