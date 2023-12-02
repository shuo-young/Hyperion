# 从所有case中对测试集进行去重获取微调训练集，将微调训练集做成alpaca格式
import json

# 打开包含所有样本的 JSON 文件
with open('/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/26/out.json', 'r') as all_samples_file:
    all_samples = json.load(all_samples_file)

print(f'所有case数：{len(all_samples)}')

# 打开包含测试集样本的 JSON 文件
with open('/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/14/test_case.json', 'r') as test_samples_file:
    test_samples = json.load(test_samples_file)

print(f'测试case数：{len(test_samples)}')

# 从所有样本中减去测试集样本
train_samples = [sample for sample in all_samples if str(sample['id']) not in [test_sample['id'] for test_sample in test_samples]]
print(f'微调训练case数：{len(train_samples)}')

# 保存
with open('ft_data_3000.json', 'w') as ft_alpaca_data:
    json.dump(train_samples, ft_alpaca_data, indent=4)

print("已去除测试数据,文件已保存")

# 打开问题
# with open("/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/12/question.json", "r", encoding="utf-8") as question_json_file:
#     question_datas = json.load(question_json_file)


# alpaca_data = []
# # 制作为alpaca格式
# for sample in train_samples:
#     category = int(sample["category"])
#     # 获取问题
#     q1 = question_datas[category-1]["q1"]

#     # 格式转换
#     alpaca_data.append({
#         "id":sample["id"],
#         "instruction":q1,
#         "input":sample["input"],
#         "output":sample["expected"]
#     })


# 保存训练集样本到新的 JSON 文件
# with open('ft_alpaca_data.json', 'w') as ft_alpaca_data:
#     json.dump(alpaca_data, ft_alpaca_data, indent=4)

# print("微调训练集已保存到 ft_alpaca_data.json")