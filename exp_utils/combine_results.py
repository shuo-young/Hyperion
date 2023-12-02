import os
import shutil

# combine outputs in two folders into one folder
folder1 = "result/wild_1"
folder2 = "result/wild_2"

# 目标文件夹路径
target_folder = "result/wild_all"

# 创建目标文件夹
if not os.path.exists(target_folder):
    os.makedirs(target_folder)

# 复制第一个文件夹的内容到目标文件夹
for root, dirs, files in os.walk(folder1):
    for file in files:
        src_file = os.path.join(root, file)
        dst_file = os.path.join(target_folder, file)
        shutil.copy2(src_file, dst_file)
        print(f"File '{file}' copied to target folder from folder1.")

# 复制第二个文件夹的内容到目标文件夹（只复制目标文件夹中不存在的文件）
for root, dirs, files in os.walk(folder2):
    for file in files:
        src_file = os.path.join(root, file)
        dst_file = os.path.join(target_folder, file)
        if not os.path.exists(dst_file):
            shutil.copy2(src_file, dst_file)
            print(f"File '{file}' copied to target folder from folder2.")

print("Folder merge completed.")
