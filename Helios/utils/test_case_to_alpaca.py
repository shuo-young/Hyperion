import json

def main():

    i=1
    
    # 提问的文件
    # question_file = "/GPUFS/nsccgz_ywang_zfd/zhongqy/llama2_finetuning_for_Dapp/experiments/6/question.json"
    question_file = "/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/6/question.json"
    # 前端输入文本
    # text_file = "/GPUFS/nsccgz_ywang_zfd/zhongqy/llama2_finetuning_for_Dapp/experiments/6/text.json"
    text_file = "/home/zhongqy/workplace/llama2_finetuning_for_Dapp/experiments/6/test_case.json"
    
    # 输出文件路径
    # out_file_path = "/GPUFS/nsccgz_ywang_zfd/zhongqy/llama2_finetuning_for_Dapp/experiments/6/out3.json"
    out_file_path = "/home/zhongqy/workplace/llama2_finetuning_for_Dapp/dataset/test_case_aplaca.json"
    

    with open(question_file, "r", encoding="utf-8") as question_json_file:
        question_datas = json.load(question_json_file)
    
    with open(text_file, "r", encoding="utf-8") as text_json_file:
        text_datas = json.load(text_json_file)
    

    # 输出结果json数组
    output_datas = []

    try:
        #遍历JSON数组
        for text in text_datas:
            print(f'处理第{i}条文本...')
            # 获取单条数据
            
            
            # 获取该前端文本对应的问题类别
            category = int(text.get("category",""))

            # 前端文本
            input_text = text.get("input", "")
            # 期望输出
            expected = text.get("expected","")
            
            # 问题
            q1 = question_datas[category-1]["q1"]
          
            
            # 两次结果都存储
            output_data = {
            "instruction": q1,
            "input":input_text,
            "output":expected
            }

            print(output_data)
            
        
            output_datas.append(output_data)
            i=i+1

    except Exception as e:
        print(f"出错了:{e}，提前保存文件")
    finally:
        # 使用with语句打开文件并将JSON对象写入文件
        with open(out_file_path, "w") as json_file:
            json.dump(output_datas, json_file, indent=4)

        print(f"已转化为apalca格式，保存到： {out_file_path}")
    


if __name__ == "__main__":
    main()