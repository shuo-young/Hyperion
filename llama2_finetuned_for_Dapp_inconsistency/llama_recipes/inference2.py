# 从控制台输入，但是无多轮对话功能
import fire
import os
import sys
import time

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


# 循环问答
while True:
    user_prompt = input("请输入提问内容 (输入 'exit' 退出): ")
    
    if user_prompt.lower() == 'exit':
        break

    # 在循环中进行推理
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
        # print(type(outputs))
        # print("==========")
        # print(outputs)
        # print("==========")
        # print(type(outputs[0]))
        # print("==========")
        # print(outputs[0])
        # print("==========")

    output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # 输出模型的回答
    print("下面是模型的输出===========================================")
    print(f"Model output:\n{output_text}")
