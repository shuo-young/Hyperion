# Helios: DApp front-end description analysis module

## module directory structure

- **dataset:** Store model fine-tuning datasets and pre training datasets (as we ultimately did not use pre training schemes, we can ignore the pre training dataset).
- **experiment:** Store experimental results. For each experimental contents:
  - If it contains an input case file, it indicates that the input case has been updated in this experiment.
  - If it contains a question file, it indicates that the question content has been updated in this experiment.
  - If the case file/question file is not included, it means that the case or question used in this experiment is the most recent case/question used in the previous experiment.
- **llama:** Llama [official hub](https://github.com/facebookresearch/llama).
- **llama-recipe:** Based on the latest version of the official llama2 fine-tuning repository (as of September 27, 2023), this is the core part of the code for this [project](https://github.com/facebookresearch/llama-recipes). There are two most important scripts in /chat_completion:
  - my_chat.py:A script for conducting specific problem inference on Dapp front-end text that competes for a specific problem
  - ask_all_question.py:A script that infers all types of problems for every piece of text
  - Please refer to the following for specific usage methods
- **llama-recipes-09-11:** As of September 11, 2023, the official llama2 fine-tuning github. In this version, the source code has been modified to solve the problem of not outputting the Lora model in some cases during the fine-tuning training process of the latest version of the repository. The following scripts are mainly used in this directory:
  - llama_finetuning.py: Fine tune llama2
- **utils:** Tool content. Contains scripts for running main commands and processing various data.

## Key experiments/directory in workflow

In order to obtain the best LLM inference results, we conducted numerous experimental attempts. Some key experimental directory contain important data. If you want to obtain the final experimental data we use, just follow the directories/files mentioned below.

### Prompt Design

In our paper, it is mentioned that our complete prompt consists of the following parts:
> { 𝑃 = { 𝑆𝑃 : 𝑅 + 𝐺𝐼 } + { 𝑈𝑃 : 𝑈𝑃<sub>𝑓𝑝</sub> +𝑈𝑃<sub>𝐶𝑜𝑇</sub> } + 𝐷 }

In order to facilitate flexible adjustment of prompts in the experiment, we have placed different parts in files or inference scripts.

The location corresponding to each part:

#### 𝑆𝑃 (𝑅 + 𝐺𝐼)

system prompt. In llama2, SP is the role assigned to llama2 during the first conversation, along with some response criteria.

Located inside the inference script: `/llama_recipes/chat_completion/ask_all_question.py` and `/llama_recipes.chat_completion/my_chat.py` ,stored in a variable named "system_role". The specific content is as follows:
> You are an expert in blockchain and smart contracts.
Always answer according to my requirements and be concise and accurate.
If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.

#### UP

user prompt.
The prompt we ultimately use is located in the `experiments/20/question.json`.

Question with category fields ranging from 1 to 4 represent our hope for LLM to provide answers on key attribute values; Question with category fields ranging from 5 to 7 represent our hope for LLM to provide a bool type answer (using the Cot method).

#### D

The front-end text of Dapp. Almost every experimental directory has its corresponding storage file. For example, for experiment 40, D is located in `experiments/40/wild_2_3_3000.json`. For each item in the object array in the JSON file,, the **input** field is the specific text.

#### Attention

In order to facilitate LLM's understanding and effectively distinguish between data and instructions in the prompt, natural language for transition was added between UP and D when concatenating the parts of the prompt in the code, as follows:
> { 𝑃 = { 𝑆𝑃 : 𝑅 + 𝐺𝐼 } + { 𝑈𝑃 : 𝑈𝑃<sub>𝑓𝑝</sub> +𝑈𝑃<sub>𝐶𝑜𝑇</sub> } + "The text I provided is:" + 𝐷 }

The following is a complete prompt example for the first category of inconsistency problem
> You are an expert in blockchain and smart contracts. Always answer according to my requirements and be concise and accurate. If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.
>
> Extract numerical information related to the rate of reward or profit from the provided text. The text I provided is:
>
> You need to enable JavaScript to run this app. Connect Connect Baked Onions MATIC Reward Pool based on a Baked Beans Fork. Home Swap How to Play Active since May 7, 2022 Plant your Onions, six times a week. Eat your onions, one time a week. If you eat your Onions too much you will stop earning! Contract 0 MATIC Wallet 0 MATIC Your ONIONS 0 ONIONS MATIC Buy Onions Your Rewards 0 MATIC PLANT ONIONS EAT ONIONS Baked Onions Details Daily Return 8% APR 2,920% Dev Fee 5% Referral Link Earn 12% of the MATIC used to Plant Onions from anyone who uses your referral link FAQs MetaMask Connect to your MetaMask Wallet WalletConnect Scan with WalletConnect to connect...

### Prompt Segmentation

Through experimentation, we find that a limit of 3000 tokens per segmentation yields the best results (compared to 500, 1000, 1500, 2000, and 4000).

The specific experimental data for Dapp text segmentation with different token lengths are located in `experiments/token_length_compare/result_compare`.

### Instruction Fine-Tuning

The final dataset in Alpaca dataset format for Lora fine-tuning is located at: `dataset/ft_dataset/exp35.json`.

This fine-tuning experiment and its related records are located at: `experiments/35`. The output file in this directory is the output result of the llama2 base model. On this basis, we corrected and streamlined the output of llama2 to achieve our expected effect, and then constructed it into a dataset in alpaca_dataset format (i.e. `dataset/ft_dataset/exp35.json`), for final fine-tuning.`log.out` is a fine-tuning log file.

## Run Step

### Environmental configuration

Create a new virtual environment and install dependencies

```bash
pip install -r requirements.txt
```

### Inference

cd inference directory

```bash
cd llama2_finetuning_for_Dapp/llama_recipes/chat_completion
```

Edit the parameters in the script that need to be used, with the main parameters being as follows:
>
> - model_name :Llama2 base model path
> - peft_model: The path of the fine-tuning Lora model
> - do_sample: Sampling method
> - question_file:The specific question content for a certain question in the JSON file
> - text_file:Dapp front-end text file
> - out_file_path:Output path JSON file
> - out_file_path_d:Output dialog JSON file

inference

```bash
# Specify using graphics cards 0 and 1 to run scripts
# Only strive to ask specific questions about the text
CUDA_VISIBLE_DEVICES=0,1 python my_chat.py
# For each text, ask all the questions
CUDA_VISIBLE_DEVICES=0,1 python ask_all_question.py
```

### Fine-tuning

cd Fine-tuning directory

```bash
cd llama2_finetuning_for_Dapp/llama-recipes-09-11
```

Configure fine-tuning parameters

Open the run.sh file and configure the main parameters

> - model_name:Llama2 base model path
> - output_dir:The path of the fine-tuning Lora model
> - dataset:The format of the dataset used for fine-tuning, specified as alpaca_dataset
> - data_path:JSON file path of datasets for fine-tuning

Execute fine-tuning scripts

```bash
nohup bash run_ft.sh > {Log path} 2>&1 &
```
