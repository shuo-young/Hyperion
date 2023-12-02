import os
import json
from collections import defaultdict


def count_inconsistencies(folder_path):
    count_of_true_keys = defaultdict(int)
    dapp_with_at_least_one_true = 0

    for dapp_folder in os.listdir(folder_path):
        dapp_folder_path = os.path.join(folder_path, dapp_folder)
        if os.path.isdir(dapp_folder_path):
            for file in os.listdir(dapp_folder_path):
                if file.endswith(".json"):
                    file_path = os.path.join(dapp_folder_path, file)
                    with open(file_path, "r") as json_file:
                        data = json.load(json_file)
                        inconsistency = data.get("inconsistency", {})

                        true_count = sum(
                            value is True for value in inconsistency.values()
                        )
                        if true_count > 0:
                            dapp_with_at_least_one_true += 1
                            count_of_true_keys[true_count] += 1

    return count_of_true_keys, dapp_with_at_least_one_true


# 示例用法
folder_path = "/pro/yangshuo/Hyperion/hyperion/evaluation_wild_all"
true_key_counts, total_dapps_with_true = count_inconsistencies(folder_path)

print("DApp counts by number of true keys:", true_key_counts)
print("Total DApps with at least one true key:", total_dapps_with_true)
