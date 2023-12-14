torchrun --nnodes 1 --nproc_per_node 2 inference.py \
--model_name /GPUFS/nsccgz_ywang_zfd/zhongqy/models/llama-2-13b-chat-hf \
--prompt_file /GPUFS/nsccgz_ywang_zfd/zhongqy/prompt_file.txt
