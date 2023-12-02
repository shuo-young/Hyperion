import pandas as pd
import json

# 读取Excel文件
def read_excel(file_path, sheet_name, input_column_name, output_column_name):
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    data = []

    for index, row in df.iterrows():
        input_1 = row[input_column_name]
        output_1 = row[output_column_name]

        # 分割input_1字符串
        prefix = "The text I provided is:"
        if prefix in input_1:
            parts = input_1.split(prefix)
            if len(parts) == 2:
                data.append({
                    "instruction": parts[0].strip(),
                    "input": parts[1].strip(),
                    "output": output_1
                })

    return data

# 保存数据到JSON文件
def save_to_json(data, output_file):
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    input_file = "/home/zhongqy/workplace/llama2_finetuning_for_Dapp/修改微调输出.xlsx"  # 请替换成实际的Excel文件路径
    sheet_name = "JSON"  # 请替换成实际的工作表名称
    input_column_name = "input_1"  # 请替换成实际的输入列名
    output_column_name = "output_ft"  # 请替换成实际的输出列名
    output_file = "output.json"  # 保存为JSON文件

    data = read_excel(input_file, sheet_name, input_column_name, output_column_name)
    save_to_json(data, output_file)
    print("运行完成！")
