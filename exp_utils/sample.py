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
copy_random_folders("exp_category_wild1123/clear", "sampling_exp/clear", 32)
copy_random_folders("exp_category_wild1123/fee", "sampling_exp/fee", 28)
copy_random_folders("exp_category_wild1123/supply", "sampling_exp/supply", 28)
copy_random_folders("exp_category_wild1123/metadata", "sampling_exp/metadata", 29)
