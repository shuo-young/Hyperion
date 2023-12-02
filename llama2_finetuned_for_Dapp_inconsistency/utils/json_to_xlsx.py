# json转为xlsx
import pandas as pd
import json

with open ("/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/1/case_in.json") as f:
    json_data = json.load(f)

# 创建一个Pandas数据框
df = pd.DataFrame(json_data)

# 将数据框保存为Excel文件
df.to_excel("output.xlsx", index=False, engine="openpyxl")
