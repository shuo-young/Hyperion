# 两轮对话自动测试
import fire
import os
import sys
import time
import json
import logging
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
# model_name = "/GPUFS/nsccgz_ywang_zfd/zhongqy/models/llama-2-13b-chat-hf"
model_name = "/mnt/data2/zhongqy/llama-2-13b-chat-hf"
# peft_model = "/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/ft/84_epoch2"
# peft_model = "/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/pre/3000/pt_lora_model"
# peft_model = "/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/pre_ft/3000_84_epoch2"
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
        
    print("模型参数：=============")
    print(f'do_sample is :{do_sample}\n')
    print(f'temperature is :{temperature}\n')
    print(f'top_p is :{top_p}\n')
    print(f'top_k is :{top_k}\n')
    print("=====================")

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
    
    # note = "第9次实验,将问题分为数值型和布尔型回答。数值型以键值对提取相关数值；布尔型通过cot回答"
    # note = "第9次实验补充实验，只优化prompt不优化text"
    note = "实验12基础上，分段从2800变为1800"
    print("开始自动化测试......")
    print(note)
    i=1
    
    
    # 提问的文件
    # question_file = "/GPUFS/nsccgz_ywang_zfd/zhongqy/llama2_finetuning_for_Dapp/experiments/6/question.json"
    question_file = "/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/12/question.json"
    # 前端输入文本
    # text_file = "/GPUFS/nsccgz_ywang_zfd/zhongqy/llama2_finetuning_for_Dapp/experiments/6/text.json"
    text_file = "/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/14/test_case.json"
    
    # 输出文件路径
    # out_file_path = "/GPUFS/nsccgz_ywang_zfd/zhongqy/llama2_finetuning_for_Dapp/experiments/6/out3.json"
    out_file_path = "/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/15/out2.json"
    
    # 日志文件==========================================================
    # log_file = "/GPUFS/nsccgz_ywang_zfd/zhongqy/llama2_finetuning_for_Dapp/experiments/6/exp.log"
    log_file = "/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/15/log2.out"
    
    # 创建一个logger
    logger = logging.getLogger(log_file)
    logger.setLevel(logging.DEBUG)

    # 创建一个handler，用于写入日志文件
    fh = logging.FileHandler(log_file)

    # 定义handler的输出格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # 给logger添加handler
    logger.addHandler(fh)

    # ==========================================================
    
    

    with open(question_file, "r", encoding="utf-8") as question_json_file:
        question_datas = json.load(question_json_file)
    
    with open(text_file, "r", encoding="utf-8") as text_json_file:
        text_datas = json.load(text_json_file)
    

    # 输出结果json数组
    output_datas = []

    try:
        #遍历JSON数组
        for text in text_datas:
            print(f'处理第{i}条文本...====================================================================================')
            # 获取单条数据
            
            # 初试上下文，即系统角色
            system_prompt = '''
You are an expert in blockchain and smart contracts.
Always answer according to my requirements and be concise and accurate.
If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.
            '''
            # system_prompt = "You are an assistant.  "
        
            user_prompt = f'''
            <s>[INST] <<SYS>>
            { system_prompt }
            <</SYS>>
            '''
            # 首次对话，上下文及为赋予的角色
            context = user_prompt
            
            # 获取该前端文本对应的问题类别
            category = int(text.get("category",""))

            # 前端文本
            input_text = text.get("input", "")
            # 期望输出
            expected = text.get("expected","")
            # id
            text_id = text.get("id","")
            # dapp name
            dapp_name = text.get("dappName","")
            
            # 问题
            q1 = question_datas[category-1]["q1"]
            # q1 = question_datas[0]["q1"]
            
            # 指定纯净输入(上下文作为单独参数输入)
            prompt1 = q1+"\nThe text I provided is:"+input_text
            # 推理
            
            # 推理，第一次答案
            single_res1,context = inference(prompt1,context)
            # single_res1 = "res1"
            print("提问：")
            print(prompt1)
            print("回答：")
            print(single_res1)
            print('\n')
            
            # 第二次推理,格式化
            # q2 = question_datas[category-1]["q2"]
            # prompt2 = q2
            # ".\nYou just need to strictly follow my requirements and provide the most concise output. Do not output any unnecessary content, such as explanations and reasons."
            # single_res2,context = inference(prompt2,context)
            # single_res2 = "res2"
            # print(q2)
            # print(single_res2)
            # print('\n')
            
            # 两次结果都存储
            output_data = {
            "category":category,
            "q1": q1,
            "input_1": system_prompt+prompt1,
            "output_1": single_res1,
            # "q2": q2,
            # "output_2": single_res2,
            "expected":expected,
            "id":text_id,
            "dappName":dapp_name,
            # "model":os.path.basename(model_name),
            "notes":note,
            "key_parameter":key_parameter,
            "correct":"",
            "evaluate":""
            }
            
            # print(output_data)
        
            output_datas.append(output_data)
            i=i+1

    except Exception as e:
        print(f"出错了:{e}，提前保存文件")
    finally:
        # 使用with语句打开文件并将JSON对象写入文件
        with open(out_file_path, "w") as json_file:
            json.dump(output_datas, json_file, indent=4)
        
        logger.info(note)
        logger.info(key_parameter)

        print(f"JSON数据已写入到文件 {out_file_path}")
    


if __name__ == "__main__":
    main()