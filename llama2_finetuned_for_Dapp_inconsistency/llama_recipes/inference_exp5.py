# 两轮对话自动测试
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
# 定义全局模型
# 在循环外部加载和初始化模型
model = None
tokenizer = None

# 定义模型参数
model_name = "/GPUFS/nsccgz_ywang_zfd/zhongqy/models/llama-2-13b-chat-hf"
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
top_k = 10
repetition_penalty = 1.0
length_penalty = 1
enable_azure_content_safety = False
enable_sensitive_topics = False
enable_salesforce_content_safety = False
max_padding_length = 4096  # 可选

key_parameter = {
    "peft_model":peft_model,
    "do_sample":do_sample,
    "temperature":temperature,
    "top_p":top_p,
    "top_k":top_k,
    "use_fast_kernels":use_fast_kernels
}

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
    
    
    # 清除输入
    # output_text.replace(user_prompt,"")
    
    # 增加回答到上下文
    context = output_text+"</s><s>[INST]"
    
    # 仅仅打印最后一次输出
    string_list = output_text.split("[/INST]")
    # 获取最后一项
    last_item = string_list[-1]
    
    return last_item,context

    # 输出模型的回答
    # print("本次提问模型回答===========================================")
    # print(last_item)




def main():
        # 加载模型
    load_my_model()
    
    global key_parameter
    
    note = "第5次测试，基于实验3，第一轮不限制回答；第二轮回答限制其格式。"
    print("开始自动化测试......")
    print(note)
    i=1
    
    
    #打开JSON文件并加载数据
    in_file_path_in = "/GPUFS/nsccgz_ywang_zfd/zhongqy/experiments/1/case_in.json"

    # 输出文件路径
    out_file_path = "/GPUFS/nsccgz_ywang_zfd/zhongqy/experiments/5/case_out_2.json"
    
    with open(in_file_path_in, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)

    # 输出结果json数组
    output_datas = []

    #遍历JSON数组
    for item in data:
        print(f'处理第{i}条数据...')
        # 获取单条数据
        
        # 初试上下文，即系统角色
        system_prompt = '''
        You are a dapp sensitive information extractor.You will need to check important attributes from the DAPP front-end text I provided"
        '''
        # system_prompt = "You are an assistant.  "
    
        user_prompt = f'''
        <s>[INST] <<SYS>>
        { system_prompt }
        <</SYS>>
        '''
        # 首次对话，上下文及为赋予的角色
        context = user_prompt
        
        
        instruction = item.get("instruction", "")
        input_data = item.get("input", "")
        
        
        expected = item.get("expected","")
        
        # 指定纯净输入(上下文作为单独参数输入)
        user_input = instruction+"\nThe input text is："+input_data
        # 推理
        
        # 推理，第一次答案
        single_res1,context = inference(user_input,context)
        
        # 第二次推理，修改user_input，增加一个问题,即示例输出
        eg = item.get("eg","")
        user_input_2 = "Please format your last round output answer."+eg+".\nYou just need to strictly follow my requirements and provide the most concise output. Do not output any unnecessary content, such as explanations and reasons."
        single_res2,context = inference(user_input_2,context)
        
        
        # 两次结果都存储
        output_data = {
        "instruction": instruction,
        "input_1": system_prompt+user_input,
        "output_1": single_res1,
        "input_2": user_input_2,
        "output_2": single_res2,
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
    


if __name__ == "__main__":
    main()