import json
import pandas as pd
from nlp.nlp import FrontEndSpecsExtractor

# 读取Excel文件
excel_file = "all_case.xlsx"  # 替换成你的Excel文件路径
df = pd.read_excel(excel_file)

# 创建一个字典来存储每个id的处理结果
results = {}

extractor = FrontEndSpecsExtractor()


# 定义一个处理output_1的函数，根据category的值来调用不同的处理函数
def process_output_1(row):
    category = row['category']
    output_1 = row['output_1']

    # 根据category的值调用不同的处理函数
    if category == '1':
        # 调用处理Category1的函数，假设为 process_category1_output(output_1)
        result = extractor.process_rate(output_1, ['reward', 'return'])
    elif category == '2':
        # 调用处理Category2的函数，假设为 process_category2_output(output_1)
        result = extractor.process_rate(output_1, ['fee'])
    elif category == '3':
        # 处理其他category的情况
        result = extractor.process_supply(output_1)
    elif category == '4':
        # 处理其他category的情况
        result = extractor.process_lock_time(output_1)
    else:
        result = None

    # 获取id并将处理结果存储到字典中
    id_value = row['id']
    if id_value in results:
        results[id_value].append(result)
    else:
        results[id_value] = [result]


# 遍历DataFrame的每一行，调用处理函数并存储结果
for index, row in df.iterrows():
    process_output_1(row)

# 打印处理结果
# 将处理结果存储为JSON文件
with open('output_results.json', 'w') as json_file:
    json.dump(results, json_file, indent=4)
