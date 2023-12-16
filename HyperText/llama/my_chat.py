# Copyright (c) Meta Platforms, Inc. and affiliates.
# This software may be used and distributed according to the terms of the Llama 2 Community License Agreement.

from typing import List, Optional

import fire

from llama import Llama, Dialog


def main(
    ckpt_dir='/GPUFS/nsccgz_ywang_zfd/zhongqy/models/llama-2-70b-chat/70B',
    tokenizer_path='/GPUFS/nsccgz_ywang_zfd/zhongqy/models/llama-2-70b-chat/tokenizer.model',
    temperature: float = 0.75,
    top_p: float = 0.9,
    max_seq_len: int = 800,
    max_batch_size: int = 4,
    max_gen_len: Optional[int] = None,
):
    """
    Entry point of the program for generating text using a pretrained model.

    Args:
        ckpt_dir (str): The directory containing checkpoint files for the pretrained model.
        tokenizer_path (str): The path to the tokenizer model used for text encoding/decoding.
        temperature (float, optional): The temperature value for controlling randomness in generation.
            Defaults to 0.6.
        top_p (float, optional): The top-p sampling parameter for controlling diversity in generation.
            Defaults to 0.9.
        max_seq_len (int, optional): The maximum sequence length for input prompts. Defaults to 512.
        max_batch_size (int, optional): The maximum batch size for generating sequences. Defaults to 8.
        max_gen_len (int, optional): The maximum length of generated sequences. If None, it will be
            set to the model's max sequence length. Defaults to None.
    """
    generator = Llama.build(
        ckpt_dir=ckpt_dir,
        tokenizer_path=tokenizer_path,
        max_seq_len=max_seq_len,
        max_batch_size=max_batch_size,
    )

    while True:
        user_input = input("You: ")
        if not user_input:
            break

        # Add the user input to the dialog
        dialog = [{"role": "user", "content": user_input}]

        # Generate a response
        result = generator.chat_completion(
            [dialog],  # type: ignore
            max_gen_len=max_gen_len,
            temperature=temperature,
            top_p=top_p,
        )[0]

        print(f"Assistant: {result['generation']['content']}\n")


if __name__ == "__main__":
    print("开始本轮聊天！")
    fire.Fire(main)
