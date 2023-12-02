import fire
import os
import sys
import time
import torch
from transformers import LlamaTokenizer
from llama_recipes.inference.model_utils import load_model, load_peft_model
import json




torch.cuda.empty_cache()

# 定义所有参数
model_name = "/GPUFS/nsccgz_ywang_zfd/zhongqy/models/llama-2-13b-chat-hf"
peft_model = False  # 可选
quantization = False
max_new_tokens = 800
seed = 42
do_sample = True
min_length = None  # 可选
use_cache = True
top_p = 0.9
temperature = 0.75
top_k = 50
repetition_penalty = 1.0
length_penalty = 1
enable_azure_content_safety = False
enable_sensitive_topics = False
enable_salesforce_content_safety = True
max_padding_length = None  # 可选
use_fast_kernels = False

# 在循环外部加载和初始化模型
model = None
tokenizer = None

# 加载模型和解码器 ===============================================================================
print("模型开始加载...")

# Set the seeds for reproducibility
torch.cuda.manual_seed(seed)
torch.manual_seed(seed)

model = load_model(model_name, quantization)

if peft_model:
    model = load_peft_model(model, peft_model)
model.eval()

if use_fast_kernels:
    try:
        from optimum.bettertransformer import BetterTransformer
        model = BetterTransformer.transform(model)
    except ImportError:
        print("Module 'optimum' not found. Please install 'optimum' it before proceeding.")

tokenizer = LlamaTokenizer.from_pretrained(model_name)

tokenizer.add_special_tokens(
    {
        "pad_token": "<PAD>",
    }
)
model.resize_token_embeddings(model.config.vocab_size + 1)



# 推理部分====================================================================================
system_prompt = "you are a assistant"
user_prompt = f'''
<s>[INST] <<SYS>>
{ system_prompt }
<</SYS>>

'''

# 循环问答
while True:
    user_input = input("请输入提问内容 (输入 'exit' 退出): ")

    if user_prompt.lower() == 'exit':
        break

    # 将用户输入添加到对话历史
    user_prompt = user_prompt + user_input + '[/INST]'


    batch = tokenizer(user_prompt, padding='max_length', truncation=True, max_length=max_padding_length, return_tensors="pt")
    batch = {k: v.to("cuda") for k, v in batch.items()}

    with torch.no_grad():
        outputs = model.generate(
            **batch,
            max_new_tokens=max_new_tokens,
            do_sample=do_sample,
            top_p=top_p,
            temperature=temperature,
            min_length=min_length,
            use_cache=use_cache,
            top_k=top_k,
            repetition_penalty=repetition_penalty,
            length_penalty=length_penalty,
        )

    output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    
    # 清除输入
    # output_text.replace(user_prompt,"")
    
    # 增加回答到上下文
    user_prompt = output_text+"</s><s>[INST]"
    
    # 仅仅打印最后一次输出
    string_list = output_text.split("[/INST]")
    # 获取最后一项
    last_item = string_list[-1]
    
    # output_text = output_text.replace(user_prompt,"")
    

    # 输出模型的回答
    print("本次提问模型回答===========================================")
    print(last_item)
    # print("完整输出：")
    # print(output_text)

    # 将模型生成的回答添加到对话历史
    # conversation_history.append({"role":"assistant","content":output_text})
