# 特殊字符转义
import json

input_string = """
Whether this text indicates the existence of the manner of clearing or withdrawing all tokens/assets by someone？
Think step by step:
First,the define of the "clearing assets" is : An act of clearing contract assets, by calling certain functions in the contract (usually only called by privileged users) to achieve the transfer of all tokens or ethers. So generally the front end will not have this kind of information.
Second，if dapp can clear the assets in the contract, there may be some descriptions like: Our platform contains a feature allowing for the transfer of all contract assets to project owner for safety reasons.This is just an example to help you understand. The actual situation is not limited to such expressions.
"""

# 转义特殊字符
def escape_special_characters(input_string):
    special_characters = {
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t',
        '\b': '\\b',
        '\f': '\\f',
        '"': '\\"',
        '\\': '\\\\',
        # 添加其他需要转义的特殊字符和转义序列
    }

    for char, escape_sequence in special_characters.items():
        input_string = input_string.replace(char, escape_sequence)

    return input_string


escaped_string = escape_special_characters(input_string)

json_output = json.dumps({"escaped_string": escaped_string}, ensure_ascii=False, indent=2)

# 保存到当前目录下的txt文件中
with open('/home/zhongqy/workplace/llama2_finetuning_for_Dapp/json_str_out.txt', 'w', encoding='utf-8') as file:
    file.write(json_output)

print("Output saved to json_str_out.txt")
