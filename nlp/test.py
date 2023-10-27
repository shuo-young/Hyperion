import json
import pandas as pd
from text_analyzer import FrontEndSpecsExtractor

excel_file = "all_case.xlsx"
df = pd.read_excel(excel_file)

results = {}

extractor = FrontEndSpecsExtractor()


def process_output_1(row):
    category = row['category']
    output_1 = row['output_1']

    if category == 1:
        result = extractor.process_reward1(output_1)
    elif category == 2:
        result = extractor.process_fee(output_1)
    elif category == 3:
        result = extractor.process_supply(output_1)
    elif category == 4:
        result = extractor.process_lock_time(output_1)
    elif category == 5:
        result = extractor.process_bool(output_1, "clear")
    elif category == 6:
        result = extractor.process_bool(output_1, "pause")
    elif category == 7:
        result = extractor.process_bool(output_1, "metadata")
    else:
        result = None

    # 获取id并将处理结果存储到字典中
    id_value = row['id']
    if id_value in results:
        results[id_value].append(result)
    else:
        results[id_value] = [result]


for index, row in df.iterrows():
    process_output_1(row)

with open('output_results.json', 'w') as json_file:
    json.dump(results, json_file, indent=4)
