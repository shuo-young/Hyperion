# 修改官方的chat脚本
import json
import fire
import os
import sys

import torch
from transformers import LlamaTokenizer

sys.path.append('/home/zhongqy/workplace/llama2_finetuning_for_Dapp/llama_recipes') 
from llama_recipes.inference.chat_utils import read_dialogs_from_file, format_tokens
from llama_recipes.inference.model_utils import load_model, load_peft_model
# from llama_recipes.inference.safety_utils import get_safety_checker

def main(
    model_name : str="/mnt/data2/zhongqy/llama-2-13b-chat-hf",
    peft_model: str=None,
    quantization: bool=False,
    max_new_tokens =800, #The maximum numbers of tokens to generate
    min_new_tokens:int=0, #The minimum numbers of tokens to generate
    prompt_file: str="/home/zhongqy/workplace/llama2_finetuning_for_Dapp/llama_recipes/chat_completion/my_chats.json",
    seed: int=42, #seed value for reproducibility
    safety_score_threshold: float=0.5,
    do_sample: bool=False, #Whether or not to use sampling ; use greedy decoding otherwise.
    use_cache: bool=True,  #[optional] Whether or not the model should use the past last key/values attentions Whether or not the model should use the past last key/values attentions (if applicable to the model) to speed up decoding.
    top_p: float=1.0, # [optional] If set to float < 1, only the smallest set of most probable tokens with probabilities that add up to top_p or higher are kept for generation.
    temperature: float=1.0, # [optional] The value used to modulate the next token probabilities.
    top_k: int=10, # [optional] The number of highest probability vocabulary tokens to keep for top-k-filtering.
    repetition_penalty: float=1.0, #The parameter for repetition penalty. 1.0 means no penalty.
    length_penalty: int=1, #[optional] Exponential penalty to the length that is used with beam-based generation.
    enable_azure_content_safety: bool=False, # Enable safety check with Azure content safety api
    enable_sensitive_topics: bool=False, # Enable check for sensitive topics using AuditNLG APIs
    enable_saleforce_content_safety: bool=False, # Enable safety check woth Saleforce safety flan t5
    use_fast_kernels: bool = False, # Enable using SDPA from PyTorch Accelerated Transformers, make use Flash Attention and Xformer memory-efficient kernels
    **kwargs
):
    
    # 加载模型============================================================
    # Set the seeds for reproducibility
    print("开始加载模型...")
    torch.cuda.manual_seed(seed)
    torch.manual_seed(seed)
    model = load_model(model_name, quantization)
    if peft_model:
        model = load_peft_model(model, peft_model)
    if use_fast_kernels:
        """
        Setting 'use_fast_kernels' will enable
        using of Flash Attention or Xformer memory-efficient kernels 
        based on the hardware being used. This would speed up inference when used for batched inputs.
        """
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
    print("加载模型完成！")
    # 加载模型完成============================================================
    
    # 以下是关键部分
    system_role = '''
You are an assistant
'''
    dialogs = [[]]
    system_content = {
                "role":"system",
                "content":system_role
            }
    dialogs[0].append(system_content)
    print(f"您给llama2赋予的角色是：{system_role}\n\n")

    # 循环问答部分
    while True:
        user_input = input("请输入提问内容 (输入 'exit' 退出):\n ")
        # 整理成dialog
        user_content = {
                "role":"user",
                "content":user_input
            }
        dialogs[0].append(user_content)

        # 推理，获得回答
        chats = format_tokens(dialogs, tokenizer)
        with torch.no_grad():
            for idx, chat in enumerate(chats):
                # 推理生成回答
                tokens= torch.tensor(chat).long()
                tokens= tokens.unsqueeze(0)
                tokens= tokens.to("cuda:0")
                outputs = model.generate(
                    input_ids=tokens,
                    max_new_tokens=max_new_tokens,
                    do_sample=do_sample,
                    top_p=top_p,
                    temperature=temperature,
                    use_cache=use_cache,
                    top_k=top_k,
                    repetition_penalty=repetition_penalty,
                    length_penalty=length_penalty,
                    **kwargs
                )

                # 包含上下文的输出
                output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                #仅提取本次回答 
                output_text = output_text.split("[/INST]")[-1]
                print(f"\nLlama回答:\n{output_text}")

                # 添加到新的上下文
                assistant_content = {
                "role":"assistant",
                "content":output_text
                }
                dialogs[0].append(assistant_content)

if __name__ == "__main__":
    fire.Fire(main)
