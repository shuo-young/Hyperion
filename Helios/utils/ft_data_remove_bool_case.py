import json

# 读取JSON文件
with open('/home/zhongqy/workplace/llama2_finetuning_for_Dapp/your_json_file.json', 'r') as file:
    data = json.load(file)

# 遍历JSON数组并删除instruction字段以"W"开头的项
data = [item for item in data if not item.get('instruction', '').startswith('W')]

# 将修改后的数据保存为新的JSON文件
with open('no_bool_ft_case.json', 'w') as file:
    json.dump(data, file, indent=4)  # indent参数可选，用于格式化输出
