model_name = '/GPUFS/nsccgz_ywang_zfd/glh/code/models/llama-2-13b-chat-hf'
prompt_file = 'ConvFinQA_test.json'
print(f'evaluation/{prompt_file.split(".")[0]}_output.json')
with open(f'evaluation/{prompt_file.split(".")[0]}_output.json', 'w')as f:
    pass    