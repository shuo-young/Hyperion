import os
import json
import shutil

# Directories and file paths
backend_dir = "result/gt_1205"
frontend_output = "nlp/result/output_gt.json"
output_dir = "evaluation_gt_1205"  # Directory to save the merged data

print("analyzed contracts")
print(len(os.listdir(backend_dir)))

count = {
    "reward": 0,
    "fee": 0,
    "supply": 0,
    "lock": 0,
    "clear": 0,
    "pause": 0,
    "metadata": 0,
}


def update_count(data):
    if data["reward"]:
        count["reward"] += 1
    if data["fee"]:
        count["fee"] += 1
    if data["supply"]:
        count["supply"] += 1
    if data["lock"]:
        count["lock"] += 1
    if data["clear"]:
        count["clear"] += 1
    if data["pause"]:
        count["pause"] += 1
    if data["metadata"]:
        count["metadata"] += 1


if not os.path.exists(output_dir):
    os.makedirs(output_dir)


# inconsistency patterns
def report_inconsistency(data):
    inconsistency = {
        "reward": False,
        "fee": False,
        "supply": False,
        "lock": False,
        "clear": False,
        "pause": False,
        "metadata": False,
    }
    # 1. reward: (1) warning and ui has reward claim
    if data["reward"]["warning"] and len(data["reward"]["ui"].keys()) > 0:
        print(data["address"])
        inconsistency["reward"] = True

    # 2. fee: (1) warning and ui don't has fee claim. TOD(2) warning and ui' fee claim is not consistent
    if data["fee"]["warning"] and not data["fee"]["ui"]["has_fee"]:
        inconsistency["fee"] = True
    if data["fee"]["warning"]:
        inconsistency["fee"] = True

    # 3. supply: (1) unlimited
    if data["supply"]["unlimited"]:
        inconsistency["supply"] = True

    if data["lock"]["backend"]:
        # print("lock")
        # print(data["address"])
        inconsistency["lock"] = True

    # 5. clear: (1) not(warning and ui)
    if data["clear"]["warning"] and not data["clear"]["ui"]:
        inconsistency["clear"] = True

    # 6. pause: (1) no(backend an ui)
    if data["pause"]["backend"] and not data["pause"]["ui"]:
        inconsistency["pause"] = True

    # 7. metadata: (1) ui and backend in ['http','base64']
    if not data["metadata"]["ui"] and data["metadata"]["backend"] in ["http", "base64"]:
        inconsistency["metadata"] = True
    return inconsistency


# Function to merge data
def merge_data(backend_data, frontend_data):
    for dapp_name, backend_info in backend_data.items():
        frontend_info = frontend_data.get(dapp_name, {})
        for key in frontend_info:
            if key in backend_info:
                # Convert non-dictionary types to dictionary
                if not isinstance(backend_info[key], dict):
                    backend_info[key] = {"backend": backend_info[key]}
                # Merge frontend data into backend data under the same key
                backend_info[key]["ui"] = frontend_info[key]
            else:
                # If the key doesn't exist in backend data, create it
                backend_info[key] = {"ui": frontend_info[key]}
        backend_data[dapp_name] = backend_info
    return backend_data


# Read frontend data
with open(frontend_output, "r") as f:
    frontend_data = json.load(f)

# Initialize a dictionary to hold backend data
backend_data = {}

# Iterate over JSON files in the backend directory
for filename in os.listdir(backend_dir):
    if filename.endswith(".json"):
        file_path = os.path.join(backend_dir, filename)
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                dapp_name = data.get("dapp_name")
                if dapp_name:
                    backend_data[dapp_name] = data
        except Exception:
            continue

# Merge the data
merged_data = merge_data(backend_data, frontend_data)

#
print(len(merged_data.keys()))

# Output the merged data
# print(json.dumps(merged_data, indent=4))


# Save the merged data into separate files
for dapp_name, data in merged_data.items():
    # Create a directory for each dapp_name
    dapp_dir = os.path.join(output_dir, dapp_name)
    if not os.path.exists(dapp_dir):
        os.makedirs(dapp_dir)

    # Get the address and create a file named after it
    address = data.get(
        "address", "default"
    )  # Use 'default' or similar if address is not available
    file_path = os.path.join(dapp_dir, f"{address}.json")
    try:
        data["inconsistency"] = report_inconsistency(data)
        update_count(data["inconsistency"])
    except Exception:
        continue

    # Write the data to the file
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

    category_dir = "exp_category_gt_1205"
    if not os.path.exists(category_dir):
        os.makedirs(category_dir)

    if data["inconsistency"]["reward"]:
        category_dapp_dir = os.path.join(category_dir, "reward")
        category_dapp = os.path.join(category_dapp_dir, dapp_name)
        if not os.path.exists(category_dapp):
            os.makedirs(category_dapp)
        file_path = os.path.join(category_dapp, f"{address}.json")
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    if data["inconsistency"]["fee"]:
        # pass
        category_dapp_dir = os.path.join(category_dir, "fee")
        category_dapp = os.path.join(category_dapp_dir, dapp_name)
        if not os.path.exists(category_dapp):
            os.makedirs(category_dapp)
        file_path = os.path.join(category_dapp, f"{address}.json")
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    if data["inconsistency"]["supply"]:
        category_dapp_dir = os.path.join(category_dir, "supply")
        category_dapp = os.path.join(category_dapp_dir, dapp_name)
        if not os.path.exists(category_dapp):
            os.makedirs(category_dapp)
        file_path = os.path.join(category_dapp, f"{address}.json")
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    if data["inconsistency"]["lock"]:
        category_dapp_dir = os.path.join(category_dir, "lock")
        category_dapp = os.path.join(category_dapp_dir, dapp_name)
        if not os.path.exists(category_dapp):
            os.makedirs(category_dapp)
        file_path = os.path.join(category_dapp, f"{address}.json")
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    if data["inconsistency"]["clear"]:
        category_dapp_dir = os.path.join(category_dir, "clear")
        category_dapp = os.path.join(category_dapp_dir, dapp_name)
        if not os.path.exists(category_dapp):
            os.makedirs(category_dapp)
        file_path = os.path.join(category_dapp, f"{address}.json")
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    if data["inconsistency"]["pause"]:
        category_dapp_dir = os.path.join(category_dir, "pause")
        category_dapp = os.path.join(category_dapp_dir, dapp_name)
        if not os.path.exists(category_dapp):
            os.makedirs(category_dapp)
        file_path = os.path.join(category_dapp, f"{address}.json")
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    if data["inconsistency"]["metadata"]:
        category_dapp_dir = os.path.join(category_dir, "metadata")
        category_dapp = os.path.join(category_dapp_dir, dapp_name)
        if not os.path.exists(category_dapp):
            os.makedirs(category_dapp)
        file_path = os.path.join(category_dapp, f"{address}.json")
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

print(count)
print(len(os.listdir(output_dir)))
