# 从控制台输入，但是无多轮对话功能
import fire
import os
import sys
import time
import json

import torch
from transformers import LlamaTokenizer

from llama_recipes.inference.safety_utils import get_safety_checker
from llama_recipes.inference.model_utils import load_model, load_peft_model

torch.cuda.empty_cache()

import os
print("debug打印：")
print(os.environ.get('PYTORCH_CUDA_ALLOC_CONF'))

# 模型参数===========================================================================
model_name = "/GPUFS/nsccgz_ywang_zfd/zhongqy/models/llama-2-13b-chat-hf"
peft_model = False  # 可选
quantization = False
max_new_tokens = 800
# prompt_file = None  # 可选
seed = 42
do_sample = True #采样
min_length = None  # 可选
use_cache = True
top_p = 1.0
temperature = 1.0
top_k = 10
repetition_penalty = 1.0
length_penalty = 1
enable_azure_content_safety = False
enable_sensitive_topics = False
enable_salesforce_content_safety = True
max_padding_length = 4096  # 可选
use_fast_kernels = False

key_parameter = {
    "peft_model":peft_model,
    "do_sample":do_sample,
    "temperature":temperature,
    "top_p":top_p,
    "top_k":top_k,
    "use_fast_kernels":use_fast_kernels
}

# 在 循环 外部加载和初始化模型
model = None
tokenizer = None
# ===========================================================================


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


# 循环问答======================================
note = "第4次测试，在第3次实验基础上，补充问题中的关键概念"
print("开始自动化测试......")
print(note)
i=1

#打开JSON文件并加载数据
in_file_path = "/GPUFS/nsccgz_ywang_zfd/zhongqy/experiments/1/case_in.json"  
# 输出文件路径
out_file_path = "/GPUFS/nsccgz_ywang_zfd/zhongqy/experiments/4/case_out.json"
with open(in_file_path, "r", encoding="utf-8") as json_file:
    data = json.load(json_file)

# 输出结果json数组
output_datas = []

#遍历JSON数组
for item in data:
    print(f'处理第{i}条数据...')
    # 获取单条数据
    instruction = item.get("instruction", "")
    input_data = item.get("input", "")
    
    expected = item.get("expected","")
    
    # 实验1 仅组合问题和描述
    # user_prompt = instruction+'\n'+input_data
    # user_prompt = user_prompt +'[/INST]'
    
    #实验2 优化prompt==========================================================
    # 赋予角色
    system_prompt = '''
    You are a dapp sensitive information extractor.You will need to check important attributes from the DAPP front-end text I provided"
    '''
    # 按照官方格式进行拼接
    user_prompt = f'''
    <s>[INST] <<SYS>>
    { system_prompt }
    <</SYS>>

    '''
    # 组合角色、问题和文本，作为用户输入
    # user_prompt = user_prompt + instruction+'\n'+input_data
    # user_prompt = user_prompt +'[/INST]'
    
    # 实验3 在试验2基础上，给出回答示例，限制输出格式=============================
    # user_prompt = user_prompt + instruction
    # eg = item.get("eg","")
    # user_prompt = user_prompt+'\nThis is the way you answer:' + eg
    # user_prompt = user_prompt+ "  The input text is："+input_data
    
    # user_prompt = user_prompt +'[/INST]'
    
        
    # 实验4 在实验3或4的基础上，针对问题，给出定义
    user_prompt = user_prompt + instruction
    
    # 概念补充
    define = item.get("define")
    user_prompt = user_prompt + "\nThis is a supplement to the definition of key concepts in the questioning:"+define+'\n'
    
    eg = item.get("eg","")
    user_prompt = user_prompt+'\nThis is the way you answer:' + eg
    user_prompt = user_prompt+ "  The input text is："+input_data
    
    user_prompt = user_prompt +'[/INST]'
    
    
    # 实验5 在实验2的基础上，将第一轮输出，作为第二轮输入，重新限制格式=============
    # 见实验4文件
    

    
    # 推理
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
    
    # 将[/INST]作为分隔符，去除输出中的输入文本
    # 仅仅打印最后一次输出
    string_list = output_text.split("[/INST]")
    # 获取最后一项纯净输出内容
    last_item = string_list[-1]
    output_text = last_item
    
    # output_text = output_text.replace(instruction,"")
    # output_text = output_text.replace(input_data,"")
    # output_text = output_text.replace(user_prompt,"")
    
    # 保存输出
    # 定义一个JSON对象
    output_data = {
        "instruction": instruction,
        "input": user_prompt,
        "output": output_text,
        "expected":expected,
        "model":os.path.basename(model_name),
        "notes":note,
        "key_parameter":key_parameter,
        "evaluate":""
    }
    
    output_datas.append(output_data)
    i=i+1
    

# 使用with语句打开文件并将JSON对象写入文件
with open(out_file_path, "w") as json_file:
    json.dump(output_datas, json_file, indent=4)

print(f"JSON数据已写入到文件 {out_file_path}")

