# 修改官方的chat脚本,对于每个case，7个问题都要问
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
    peft_model: str="/mnt/data2/zhongqy/models/ft/exp35/all_ft_case_epoch9",
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
    
    #================================================================================================================

    # if prompt_file is not None:
    #     assert os.path.exists(
    #         prompt_file
    #     ), f"Provided Prompt file does not exist {prompt_file}"

    #     # 实际上返回的也是json.load的结果
    #     dialogs= read_dialogs_from_file(prompt_file)

    # elif not sys.stdin.isatty():
    #     dialogs = "\n".join(sys.stdin.readlines())
    # else:
    #     print("No user prompt provided. Exiting.")
    #     sys.exit(1)

    # print(f"User dialogs:\n{dialogs}")
    # print("\n==================================\n")


    # 加载模型============================================================
    # 关键参数，保存在运行结果中
    key_parameter = {
    "model_name":model_name,
    "peft_model":peft_model,
    "do_sample":do_sample,
    "temperature":temperature,
    "top_p":top_p,
    "top_k":top_k,
    }
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
    
    # 指定文件输入===========================================================
    question_file = "/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/20/question.json" # 具体问题文件
    text_file = "/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/41/wild4_wild5.json" # 前端输入文本
    out_file_path = "/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/41/exp41_out.json" # 输出文件路径
    out_file_path_d = "/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/41/exp41_out_dialog.json"# dialog写出路径

    with open(question_file, "r", encoding="utf-8") as question_json_file:
        question_datas = json.load(question_json_file)
    
    with open(text_file, "r", encoding="utf-8") as text_json_file:
        text_datas = json.load(text_json_file)

    # 推理部分
    output_datas = [] # 保存结果的数组
    all_dialog = [] # 所有dialog
    print(f"texts总数：{len(text_datas)}\n")

    try:
        for index,text in enumerate(text_datas):
            
            # 加载到上次的地方
            # if index+1 < 310:
            #     continue

            print(f'\n处理第{index+1}条文本...====================================================================================')

            # 指定系统角色
            system_role = '''
You are an expert in blockchain and smart contracts.
Always answer according to my requirements and be concise and accurate.
If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.
'''

            # 1.获取文本的各项内容
            category = int(text.get("category",""))
            input_text = text.get("input", "")
            expected = text.get("expected","")
            text_id = int(text.get("id",""))
            dapp_name = text.get("dappName","")
            
            # 获取问题
            # 对于每个text，这里需要分别问7个问题
            for q_index,question in enumerate(question_datas):
                
                print(f'开始问第{index+1}条文本的第{q_index+1}个问题\n')

                q1 = question["q1"]
                # 创建字典，每次都是一个新的对话
                
                # q1 = question_datas[category-1]["q1"]

                # 2.准备dialogs
                # 创建字典，每次都是一个新的对话
                dialogs = [[]]
                # 系统角色
                system_content = {
                    "role":"system",
                    "content":system_role
                }
                print(f"\n系统角色:{system_role}")

                # 用户提问
                user_prompt = q1 + "\nThe text I provided is:"+input_text
                user_content = {
                    "role":"user",
                    "content":user_prompt
                }
                print(f"\nuser提问:\n{user_prompt}")

                # 添加到对话历史
                dialogs[0].append(system_content)
                dialogs[0].append(user_content)

                # 3.基于dialogs进行推理
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

                        output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

                        # 只取回答部分
                        output_text = output_text.split("[/INST]")[-1]
                        print(f"\n模型回答:\n{output_text}")
                        print("\n============================================================\n")
                        
                        # 将模型回答保存在dialog中
                        assistant_content = {
                            "role":"assistant",
                            "content":output_text
                        }
                        dialogs[0].append(assistant_content)

                        # 如果要添加多轮对话，在这之后进行...............

                        # 保存结果到output_data
                        output_data = {
                            "key_parameter":key_parameter,
                            "id":text_id,
                            "dappName":dapp_name,
                            "category":category,
                            "question_category":q_index+1,# 记录问题的类型
                            "system_role":system_role,
                            "input_1": user_prompt,
                            "output_1": output_text,
                            "expected":expected,
                            "correct":"",
                            "evaluate":""
                        }
                        output_datas.append(output_data)

                        # dialog也保存
                        all_dialog.append(dialogs[0])

                        # 直接保存到文件
                        # 使用with语句打开文件并将JSON对象写入文件
                        with open(out_file_path, "w") as json_file:
                            json.dump(output_datas, json_file, indent=4)

                        print(f"JSON数据已写入到文件 {out_file_path}")
              
            print(f'第{index+1}条文本处理结束...====================================================================================')

    except Exception as e:
        print(f"出错了:{e}，文件已保存")
    finally:
        print("完美，没有出错运行程序！")
        # 使用with语句打开文件并将JSON对象写入文件
        # with open(out_file_path, "w") as json_file:
        #     json.dump(output_datas, json_file, indent=4)
        
        # # logger.info(note)
        # # logger.info(key_parameter)

        # print(f"JSON数据已写入到文件 {out_file_path}")

        # 将dialog也写入
        # with open(out_file_path_d, "w") as json_file:
        #     json.dump(all_dialog, json_file, indent=4)

if __name__ == "__main__":
    fire.Fire(main)
