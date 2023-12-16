# Copyright (c) Meta Platforms, Inc. and affiliates.
# This software may be used and distributed according to the terms of the Llama 2 Community License Agreement.

# from accelerate import init_empty_weights, load_checkpoint_and_dispatch

import fire
import torch
import os
import json
import sys
import time
from typing import List
from tqdm import tqdm
from transformers import LlamaTokenizer
# from safety_utils import get_safety_checker
from model_utils import load_model, load_peft_model, load_llama_from_config

def main(
    model_name,
    peft_model: str=None,
    quantization: bool=False,
    max_new_tokens =1000, #The maximum numbers of tokens to generate
    prompt_file: str=None,
    seed: int=42, #seed value for reproducibility
    do_sample: bool=True, #Whether or not to use sampling ; use greedy decoding otherwise.
    min_length: int=10, #The minimum length of the sequence to be generated, input prompt + min_new_tokens
    use_cache: bool=True,  #[optional] Whether or not the model should use the past last key/values attentions Whether or not the model should use the past last key/values attentions (if applicable to the model) to speed up decoding.
    top_p: float=1.0, # [optional] If set to float < 1, only the smallest set of most probable tokens with probabilities that add up to top_p or higher are kept for generation.
    temperature: float=1.0, # [optional] The value used to modulate the next token probabilities.
    top_k: int=10, # [optional] The number of highest probability vocabulary tokens to keep for top-k-filtering.
    repetition_penalty: float=1.0, #The parameter for repetition penalty. 1.0 means no penalty.
    length_penalty: int=1, #[optional] Exponential penalty to the length that is used with beam-based generation. 
    enable_azure_content_safety: bool=False, # Enable safety check with Azure content safety api
    enable_sensitive_topics: bool=False, # Enable check for sensitive topics using AuditNLG APIs
    enable_salesforce_content_safety: bool=True, # Enable safety check with Salesforce safety flan t5
    max_padding_length: int=4096, # the max padding length to be used with tokenizer padding the prompts.
    use_fast_kernels: bool = False, # Enable using SDPA from PyTroch Accelerated Transformers, make use Flash Attention and Xformer memory-efficient kernels
    batch_size: int=1,
    output_path: str=None,
    **kwargs
):
   
    if prompt_file == None:
            #user_prompt_list = ['我家孩子得了癫痫病应该怎么办好? 　　我家孩子得了癫痫病应该怎么办好?面色苍白，面无表情，手中持物掉落，呼之不应。孩子得了癫痫病怎么办?',"为何韩剧《主君的太阳》这么火，评价如此高？豆瓣评分8.7，优酷评分9.3设定是恐怖加搞笑，傲娇富二代和可爱傻大姐该剧满足了怎样的心理需求？","王者荣耀怎么玩好王昭君？"]
        user_prompt_list = ['Do you know  Professor.Yanlin Wang in Sun Yat-sen University?',"Do you know  Professor.Yanlin Wang's email?"]
        conv_list = [(idx,0) for idx in range(len(user_prompt_list))]
    elif "json" in prompt_file:
        with open(prompt_file,'r')as f:
            user_prompt_list = json.load(f)

        # with open('conv_list.json','r')as f:
        #     conv_list = json.load(f)      
    else:
        if prompt_file is not None:
            assert os.path.exists(
                prompt_file
            ), f"Provided Prompt file does not exist {prompt_file}"
            with open(prompt_file, "r") as f:
                user_prompt_list = "\n".join(f.readlines())
        elif not sys.stdin.isatty():
            user_prompt_list = "\n".join(sys.stdin.readlines())
        else:
            print("No user prompt provided. Exiting.")
            sys.exit(1)
    
    # # Set the seeds for reproducibility
    # torch.cuda.manual_seed(seed)
    # torch.manual_seed(seed)
    #model = load_model(model_name, quantization, use_fast_kernels)
    model = load_model(model_name, quantization)
    # if peft_model:
    #     model = load_peft_model(model, peft_model)

    # model.eval()
    
    # if use_fast_kernels:
    #     """
    #     Setting 'use_fast_kernels' will enable
    #     using of Flash Attention or Xformer memory-efficient kernels 
    #     based on the hardware being used. This would speed up inference when used for batched inputs.
    #     """
    #     try:
    #         from optimum.bettertransformer import BetterTransformer
    #         model = BetterTransformer.transform(model)    
    #     except ImportError:
    #         print("Module 'optimum' not found. Please install 'optimum' it before proceeding.")

    tokenizer = LlamaTokenizer.from_pretrained(model_name)
    tokenizer.add_special_tokens(
        {
            "pad_token": "<PAD>",
        }
    )
    model.resize_token_embeddings(model.config.vocab_size + 1) 
    
    # safety_checker = get_safety_checker(enable_azure_content_safety,
    #                                     enable_sensitive_topics,
    #                                     enable_salesforce_content_safety,
    #                                     )

    # # Safety check of the user prompt
    # safety_results = [check(user_prompt) for check in safety_checker]
    # are_safe = all([r[1] for r in safety_results])
    # if are_safe:
    #     print("User prompt deemed safe.")
    #     print(f"User prompt:\n{user_prompt}")
    # else:
    #     print("User prompt deemed unsafe.")
    #     for method, is_safe, report in safety_results:
    #         if not is_safe:
    #             print(method)
    #             print(report)
    #     print("Skipping the inference as the prompt is not safe.")
    #     sys.exit(1)  # Exit the program with an error status
        
    if peft_model:
        model = load_peft_model(model, peft_model)

    model.eval()
    answer_list = []
    # user_prompt_list = user_prompt_list[:5]
    for batch_idx in tqdm(range(0,len(user_prompt_list),batch_size)):
        # user_prompt = user_prompt_list[batch_idx:min(batch_idx+batch_size,len(user_prompt_list))]

        user_prompt = user_prompt_list[batch_idx:min(batch_idx+batch_size,len(user_prompt_list))][0]
        # session_idx = user_prompt[batch_idx]
        # print(len(user_prompt))
        # print(session_idx)
        # for s_idx in range(session_idx):
            # user_prompt = user_prompt.replace("{answer"+str(s_idx)+"}","\na{}: ".format(s_idx)+answer_list[-session_idx+s_idx])
        # print(user_prompt)
        batch = tokenizer(user_prompt, padding='max_length', truncation=True,max_length=max_padding_length,return_tensors="pt")
        batch = {k: v.to("cuda") for k, v in batch.items()}
        #batch = tokenizer(user_prompt, padding='longest',return_tensors="pt").to('cuda')
        #print(batch['input_ids'].shape)#(batch_siz)
        # batch = tokenizer(user_prompt, padding='max_length', truncation=True,max_length=max_padding_length,return_tensors="pt")

        # batch = {k: v.to("cuda") for k, v in batch.items()}
        start = time.perf_counter()
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
                **kwargs 
            )
        e2e_inference_time = (time.perf_counter()-start)*1000
        print(f"the inference time is {e2e_inference_time} ms")
        #output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        #output_text  = tokenizer.batch_decode(outputs)
        output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(output_text)
        output_text = output_text.replace(user_prompt,"")
        print(output_text)
        answer_list.append(output_text)
    # Safety check of the model output
    # safety_results = [check(output_text) for check in safety_checker]
    # are_safe = all([r[1] for r in safety_results])
    # if are_safe:
    #     print("User input and model output deemed safe.")
    #     print(f"Model output:\n{output_text}")
    # else:
    #     print("Model output deemed unsafe.")
    #     for method, is_safe, report in safety_results:
    #         if not is_safe:
    #             print(method)
    #             print(report)
    with open(output_path, 'w')as f:
        json.dump(answer_list,f)       
        # f.write(output_path)

if __name__ == "__main__":
    fire.Fire(main)
