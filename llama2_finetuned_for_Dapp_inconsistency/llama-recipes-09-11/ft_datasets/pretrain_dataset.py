# Copyright (c) Meta Platforms, Inc. and affiliates.
# This software may be used and distributed according to the terms of the Llama 2 Community License Agreement.

# For dataset details visit: https://crfm.stanford.edu/2023/03/13/alpaca.html

import copy
import json
import os
import torch

from sentencepiece import SentencePieceProcessor
from torch.utils.data import Dataset
from typing import List




class PretrainDataset(Dataset):
    def __init__(self, dataset_config, tokenizer, partition="train", max_words=30):
        self.ann = json.load(open(dataset_config.data_path))
        if partition == "train":
            self.ann = self.ann
        else:
            self.ann = self.ann[:200]

        self.max_words = max_words
        # tokenizer = Tokenizer(model_path=model_path + "./tokenizer.model")
        self.tokenizer = tokenizer
        # self.tokenizer1 = tokenizer

    def __len__(self):
        return len(self.ann)

    def __getitem__(self, index):
        IGNORE_INDEX = -100  # The default setting in CrossEntropyLoss


        ann = self.ann[index]
        text = ann['text']
        text = self.tokenizer.encode(text)
        text.append(self.tokenizer.eos_token_id)
        text = torch.tensor(
            text, dtype=torch.int64
        )

        padding = self.max_words - text.shape[0]
        if padding > 0:
            text = torch.cat((text, torch.zeros(padding, dtype=torch.int64) - 1))
        elif padding < 0:
            text = text[: self.max_words]
        labels = copy.deepcopy(text)
       
        text_mask = text.ge(0)
        label_mask = labels.ge(0)
        text[~text_mask] = 0
        labels[~label_mask] = IGNORE_INDEX
        text_mask = text_mask.float()
        label_mask = label_mask.float()
       
        return {
            "input_ids": text,
            "labels": labels,
            "attention_mask":text_mask,
        }
