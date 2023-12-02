# 对llama2聊天进行了一定封装
import fire
import os
import sys
import time
import torch
from transformers import LlamaTokenizer
from llama_recipes.inference.model_utils import load_model, load_peft_model
import json

# 定义全局模型
# 在循环外部加载和初始化模型
model = None
tokenizer = None

# 定义模型参数
model_name = "/mnt/data2/zhongqy/llama-2-13b-chat-hf"
peft_model = False  # 可选
quantization = False
seed = 42
use_fast_kernels = False

# 推理参数 
max_new_tokens = 800
do_sample = True
min_length = None  # 可选
use_cache = True
top_p = 1.0
temperature = 1.0
top_k = 1
repetition_penalty = 1.0
length_penalty = 1
enable_azure_content_safety = False
enable_sensitive_topics = False
enable_salesforce_content_safety = True
max_padding_length = None  # 可选

def load_my_model():
    global model,tokenizer
    global model_name, peft_model, quantization, seed, use_fast_kernels
    global max_new_tokens, do_sample, min_length, use_cache, top_p
    global temperature, top_k, repetition_penalty, length_penalty
    global enable_azure_content_safety, enable_sensitive_topics
    global enable_salesforce_content_safety, max_padding_length
    torch.cuda.empty_cache()

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
    
    print("模型加载完毕！")



# 推理部分====================================================================================
def inference(user_input,context):
    global model,tokenizer
    global model_name, peft_model, quantization, seed, use_fast_kernels
    global max_new_tokens, do_sample, min_length, use_cache, top_p
    global temperature, top_k, repetition_penalty, length_penalty
    global enable_azure_content_safety, enable_sensitive_topics
    global enable_salesforce_content_safety, max_padding_length

    # 将用户输入添加到对话历史
    context = context + user_input + '[/INST]'


    batch = tokenizer(context, padding='max_length', truncation=True, max_length=max_padding_length, return_tensors="pt")
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
    
    new_context = context
    
    # 清除输入
    # output_text.replace(user_prompt,"")
    
    # 增加回答到上下文
    context = output_text+"</s><s>[INST]"
    
    # 仅仅打印最后一次输出
    string_list = output_text.split("[/INST]")
    
    # 获取最后一项
    last_item = string_list[-1]

    print("调整之后的上下文：")
    new_context = new_context + last_item + "</s><s>[INST]"
    # print(new_context)
    
    return last_item,new_context

    # 输出模型的回答
    # print("本次提问模型回答===========================================")
    # print(last_item)



def main():
    # 加载模型
    load_my_model()
    # 定义模型角色
    system_prompt = "you are a assistant"
    
    user_prompt = f'''
    <s>[INST] <<SYS>>
    { system_prompt }
    <</SYS>>
    '''
    # 首次对话，上下文及为赋予的角色
    context = user_prompt
    
    while True:
        user_input = input("请输入提问内容 (输入 'exit' 退出):\n ")

        if user_prompt.lower() == 'exit':
            break
        
        # 推理，第一个参数为纯净的该答案回答，第二个为对话上下文
        single_res,context = inference(user_input,context)
        
        print("模型回答：")
        print(single_res)
        # print("上下文是：")
        # print(context)
    

if __name__ == "__main__":
    main()