import os
from transformers import AutoTokenizer
from transformers import LlamaTokenizer
from tqdm import tqdm

def count_tokens_in_dir(directory, model_name):

    tokenizer = LlamaTokenizer.from_pretrained(model_name)
    # tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    
    total_tokens = 0

    for filename in tqdm(os.listdir(directory)):
        if filename.endswith('.txt'):
            # print(os.path.join(directory, filename))
            with open(os.path.join(directory, filename), 'r', encoding='utf-8') as f:
                text = f.read()
                tokens = tokenizer.tokenize(text)
                total_tokens += len(tokens)

    return total_tokens

# 使用你的分词器和目录名替换下面的值
model_name = '/mnt/data2/zhongqy/llama-2-13b-chat-hf'  # 模型名称
directory = '/home/zhongqy/workplace/preTrainData/text/text'  # 目录路径

total_tokens = count_tokens_in_dir(directory, model_name)
print(f'Total tokens in directory: {total_tokens}')
