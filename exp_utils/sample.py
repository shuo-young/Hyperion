import os
import shutil
import random


def copy_random_folders(src_dir, dest_dir, num_folders):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    # 获取源目录中所有子文件夹
    all_folders = [
        f for f in os.listdir(src_dir) if os.path.isdir(os.path.join(src_dir, f))
    ]

    # 随机选择指定数量的文件夹
    selected_folders = random.sample(all_folders, min(num_folders, len(all_folders)))

    for folder in selected_folders:
        src_folder_path = os.path.join(src_dir, folder)
        dest_folder_path = os.path.join(dest_dir, folder)

        # 复制文件夹
        shutil.copytree(src_folder_path, dest_folder_path)
        print(f"Copied folder: {src_folder_path} to {dest_folder_path}")


# 示例用法
copy_random_folders(
    "exp_category_wild_1205/clear", "sampling_exp/clear", 67
)  # 35+32=67
copy_random_folders("exp_category_wild_1205/fee", "sampling_exp/fee", 44)  # 28+16=44
copy_random_folders(
    "exp_category_wild_1205/supply", "sampling_exp/supply", 60
)  # 28+32=60
copy_random_folders(
    "exp_category_wild_1205/metadata", "sampling_exp/metadata", 49
)  # 29+20=49
copy_random_folders("exp_category_wild_1205/pause", "sampling_exp/pause", 34)
