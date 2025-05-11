import sys
from pathlib import Path
import json

root_path = str(Path(__file__).resolve().parent)
sys.path.append(root_path)

# from module_task.psi import psi_csv
from utils.yaml_util import read_yaml, write_yaml

data_ii: dict = read_yaml(root_path + "/JobConfig/output_psi_input_data.yaml")

# psi_csv(**data_ii["param"])


a= json.dumps(data_ii["param"])
print(a)

aa = {"ay":a}

ac= json.dumps(aa)
print(ac)