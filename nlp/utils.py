import json
import pandas as pd
from text_analyzer import FrontEndSpecsExtractor

excel_file = "dataset/all_case_2.xlsx"
df = pd.read_excel(excel_file)

results = {}

extractor = FrontEndSpecsExtractor()


def merge_dicts(dict1, dict2):
    """merge two dict"""
    for key, value in dict2.items():
        if key in dict1:
            if isinstance(value, bool):
                dict1[key] = dict1[key] or value
            elif isinstance(value, list):
                dict1[key].extend(value)
            elif isinstance(value, float):
                if not isinstance(dict1[key], list):
                    dict1[key] = [dict1[key]]
                elif value not in dict1.values():
                    dict1[key].append(value)
        else:
            dict1[key] = value
    return dict1


def process_output_1(row):
    category = row['category']
    output_1 = row['output_1']

    if category == 1:
        result = extractor.process_reward(output_1)
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

    # merge results of the same id
    id_value = row['id']
    if id_value in results:
        results[id_value] = merge_dicts(results[id_value], result)
    else:
        results[id_value] = result


for index, row in df.iterrows():
    process_output_1(row)

with open('result/output_results_4.json', 'w') as json_file:
    json.dump(results, json_file, indent=4)
