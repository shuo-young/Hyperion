import json

# 读取JSON文件
with open('your_json_file.json', 'r') as file:
    data = json.load(file)

# 删除id列
for item in data:
    if 'id' in item:
        del item['id']

# 将修改后的数据保存为新的JSON文件
with open('new_json_file.json', 'w') as file:
    json.dump(data, file, indent=4)  # indent参数可选，用于格式化输出
