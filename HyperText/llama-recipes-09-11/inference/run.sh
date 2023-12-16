# #!/bin/bash

# python eval_inference.py \
#     --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/llama-2-13b-chat-hf \
#     --prompt_file ConvFinQA_test.json \
#     --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/raw_llama2_model.json \
#     --batch_size 1 \
#     --top_p 0.5 \
#     --top_k 50 \
#     --temperature 0.2 2>&1|tee raw_llama2_model.log

# python eval_inference.py \
#     --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/llama-2-13b-chat-hf \
#     --peft_model /GPUFS/nsccgz_ywang_zfd/glh/code/models/2048_13b_r_8_no_quantization_batch_size_256_micro_bs_16_json_ConvFinQA_epoch2 \
#     --prompt_file ConvFinQA_test.json \
#     --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/lora_epoch_2.json \
#     --batch_size 1 \
#     --top_p 0.5 \
#     --top_k 50 \
#     --temperature 0.2 2>&1|tee lora_epoch_2.log

# python eval_inference.py \
#     --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/llama-2-13b-chat-hf \
#     --peft_model /GPUFS/nsccgz_ywang_zfd/glh/code/models/2048_13b_r_8_no_quantization_batch_size_256_micro_bs_16_json_ConvFinQA_epoch0 \
#     --prompt_file ConvFinQA_test.json \
#     --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/lora_epoch_0.json \
#     --batch_size 1 \
#     --top_p 0.5 \
#     --top_k 50 \
#     --temperature 0.2 2>&1|tee lora_epoch_0.log

# python eval_inference.py \
#     --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/chinese-alpaca-2-13b \
#     --peft_model /GPUFS/nsccgz_ywang_zfd/glh/code/models/23_08_29_epoch0 \
#     --prompt_file /GPUFS/nsccgz_ywang_zfd/glh/code/datapreprocess/test.json \
#     --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/test_chinese_lora_epoch_0.json \
#     --batch_size 1 \
#     --top_p 0.5 \
#     --top_k 50 \
#     --temperature 0.2 2>&1|tee test_chinese_lora_epoch_0.log

# python eval_inference.py \
#     --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/chinese-alpaca-2-13b \
#     --peft_model /GPUFS/nsccgz_ywang_zfd/glh/code/models/23_08_29_epoch1 \
#     --prompt_file /GPUFS/nsccgz_ywang_zfd/glh/code/datapreprocess/test.json \
#     --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/test_chinese_lora_epoch_1.json \
#     --batch_size 1 \
#     --top_p 0.5 \
#     --top_k 50 \
#     --temperature 0.2 2>&1|tee test_chinese_lora_epoch_1.log

# python eval_inference.py \
#     --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/chinese-alpaca-2-13b \
#     --peft_model /GPUFS/nsccgz_ywang_zfd/glh/code/models/23_08_29_epoch2 \
#     --prompt_file /GPUFS/nsccgz_ywang_zfd/glh/code/datapreprocess/test.json \
#     --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/test_chinese_lora_epoch_2.json \
#     --batch_size 1 \
#     --top_p 0.5 \
#     --top_k 50 \
#     --temperature 0.2 2>&1|tee test_chinese_lora_epoch_2.log
    
# python eval_inference.py \
#     --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/chinese-alpaca-2-13b \
#     --prompt_file /GPUFS/nsccgz_ywang_zfd/glh/code/datapreprocess/test.json \
#     --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/test_chinese_llama2.json \
#     --batch_size 1 \
#     --top_p 0.95 \
#     --top_k 50 \
#     --temperature 0.7 2>&1|tee test_chinese_llama2_top_p_0.95_temperature_0.7.log

# python eval_inference.py \
#     --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/chinese-alpaca-2-13b \
#     --peft_model /GPUFS/nsccgz_ywang_zfd/glh/code/models/23_08_29_epoch0 \
#     --prompt_file /GPUFS/nsccgz_ywang_zfd/glh/code/datapreprocess/test.json \
#     --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/test_chinese_lora_epoch_0_top_p_0.95_temperature_0.7.json \
#     --batch_size 1 \
#     --top_p 0.95 \
#     --top_k 50 \
#     --temperature 0.7 2>&1|tee test_chinese_lora_epoch_0_top_p_0.95_temperature_0.7.log

# python eval_inference.py \
#     --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/chinese-alpaca-2-13b \
#     --peft_model /GPUFS/nsccgz_ywang_zfd/glh/code/models/23_08_29_epoch1 \
#     --prompt_file /GPUFS/nsccgz_ywang_zfd/glh/code/datapreprocess/test.json \
#     --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/test_chinese_lora_epoch_1_top_p_0.95_temperature_0.7.json \
#     --batch_size 1 \
#     --top_p 0.95 \
#     --top_k 50 \
#     --temperature 0.7 2>&1|tee test_chinese_lora_epoch_1_top_p_0.95_temperature_0.7.log

# python eval_inference.py \
#     --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/chinese-alpaca-2-13b \
#     --peft_model /GPUFS/nsccgz_ywang_zfd/glh/code/models/23_08_29_epoch2 \
#     --prompt_file /GPUFS/nsccgz_ywang_zfd/glh/code/datapreprocess/test.json \
#     --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/test_chinese_lora_epoch_2_top_p_0.95_temperature_0.7.json \
#     --batch_size 1 \
#     --top_p 0.95 \
#     --top_k 50 \
#     --temperature 0.7 2>&1|tee test_chinese_lora_epoch_2_top_p_0.95_temperature_0.7.log

# python eval_inference.py \
#     --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/llama-2-13b-chat-hf \
#     --prompt_file /GPUFS/nsccgz_ywang_zfd/glh/code/datapreprocess/test.json \
#     --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/test_llama2_top_p_0.95_temperature_0.7.json \
#     --batch_size 1 \
#     --top_p 0.95 \
#     --top_k 50 \
#     --temperature 0.7 2>&1|tee test_llama2_top_p_0.95_temperature_0.7.log
    
python eval_inference.py \
    --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/chinese-alpaca-2-13b \
    --prompt_file /GPUFS/nsccgz_ywang_zfd/glh/code/datapreprocess/test.json \
    --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/test_chinese_llama2_top_p_0.95_temperature_1.json \
    --batch_size 1 \
    --top_p 0.95 \
    --top_k 50 \
    --temperature 1 2>&1|tee test_chinese_llama2_top_p_0.95_temperature_1.log

python eval_inference.py \
    --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/chinese-alpaca-2-13b \
    --peft_model /GPUFS/nsccgz_ywang_zfd/glh/code/models/23_08_29_epoch0 \
    --prompt_file /GPUFS/nsccgz_ywang_zfd/glh/code/datapreprocess/test.json \
    --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/test_chinese_lora_epoch_0_top_p_0.95_temperature_1.json \
    --batch_size 1 \
    --top_p 0.95 \
    --top_k 50 \
    --temperature 1 2>&1|tee test_chinese_lora_epoch_0_top_p_0.95_temperature_1.log

python eval_inference.py \
    --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/chinese-alpaca-2-13b \
    --peft_model /GPUFS/nsccgz_ywang_zfd/glh/code/models/23_08_29_epoch1 \
    --prompt_file /GPUFS/nsccgz_ywang_zfd/glh/code/datapreprocess/test.json \
    --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/test_chinese_lora_epoch_1_top_p_0.95_temperature_1.json \
    --batch_size 1 \
    --top_p 0.95 \
    --top_k 50 \
    --temperature 1 2>&1|tee test_chinese_lora_epoch_1_top_p_0.95_temperature_1.log

python eval_inference.py \
    --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/chinese-alpaca-2-13b \
    --peft_model /GPUFS/nsccgz_ywang_zfd/glh/code/models/23_08_29_epoch2 \
    --prompt_file /GPUFS/nsccgz_ywang_zfd/glh/code/datapreprocess/test.json \
    --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/test_chinese_lora_epoch_2_top_p_0.95_temperature_1.json \
    --batch_size 1 \
    --top_p 0.95 \
    --top_k 50 \
    --temperature 1 2>&1|tee test_chinese_lora_epoch_2_top_p_0.95_temperature_1.log

python eval_inference.py \
    --model_name /GPUFS/nsccgz_ywang_zfd/glh/code/models/llama-2-13b-chat-hf \
    --prompt_file /GPUFS/nsccgz_ywang_zfd/glh/code/datapreprocess/test.json \
    --output_path /GPUFS/nsccgz_ywang_zfd/glh/code/llama-recipes/inference/evaluation/test_llama2_top_p_0.95_temperature_1.json \
    --batch_size 1 \
    --top_p 0.95 \
    --top_k 50 \
    --temperature 1 2>&1|tee test_llama2_top_p_0.95_temperature_1.log