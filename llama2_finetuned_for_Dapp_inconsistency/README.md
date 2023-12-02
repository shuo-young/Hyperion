# Dapp front-end text llama2 detection project

## project directory structure
- **dataset：** Store model fine-tuning datasets and pre training datasets (as we ultimately did not use pre training schemes, we can ignore the pre training dataset).
- **experiment：** Store experimental results. For each experimental contents：
  - If it contains an input case file, it indicates that the input case has been updated in this experiment.
  - If it contains a question file, it indicates that the question content has been updated in this experiment.
  - If the case file/question file is not included, it means that the case or question used in this experiment is the most recent case/question used in the previous experiment.
- **llama：** Llama official hub。[Github address](https://github.com/facebookresearch/llama)
 - **llama-recipe：** Based on the latest version of the official llama2 fine-tuning repository (as of September 27, 2023), this is the core part of the code for this project.[Github address](https://github.com/facebookresearch/llama-recipes) There are two most important scripts in /chat_completion:
    - my_chat.py：A script for conducting specific problem inference on Dapp front-end text that competes for a specific problem
    - ask_all_question.py：A script that infers all types of problems for every piece of text
    - Please refer to the following for specific usage methods
- **llama-recipes-09-11：** As of September 11, 2023, the official llama2 fine-tuning github. In this version, the source code has been modified to solve the problem of not outputting the Lora model in some cases during the fine-tuning training process of the latest version of the repository. The following scripts are mainly used in this directory:
    - llama_finetuning.py：Fine tune llama2
- **utils：** Tool content. Contains scripts for running main commands and processing various data.

## run step
### Environmental configuration
Create a new virtual environment and install dependencies
```bash
pip install -r requirements.txt
```
### inference
cd inference directory
```bash
cd llama2_finetuning_for_Dapp/llama_recipes/chat_completion
```
Edit the parameters in the script that need to be used, with the main parameters being as follows:
> - model_name :Llama2 base model path
> - peft_model: The path of the fine-tuning Lora model
> - do_sample: Sampling method
> - question_file：The specific question content for a certain question in the JSON file
> - text_file:Dapp front-end text file
> - out_file_path：Output path JSON file
> - out_file_path_d：Output dialog JSON file

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

> - model_name：Llama2 base model path
> - output_dir：The path of the fine-tuning Lora model
> - dataset：The format of the dataset used for fine-tuning, specified as alpaca_dataset
> - data_path：JSON file path of datasets for fine-tuning

Execute fine-tuning scripts
```bash
nohup bash run_ft.sh > {Log path} 2>&1 &
```

## Key experiments/documents
### exp20
The final questioning methods for the 7 types of problems have been determined,located in question.json. Complete prompt= SP (located in the inference code) + UP (located in the question. json file) + "The text I provided is:" (located in the inference script) + Dapp text (located in text. json)
### exp35
The final fine-tuning plan used.Firstly, the cases used for fine-tuning were organized, and the llama2 base model was used to infer these cases and generate ft_data_out.json, 将convert it into an xlsx file, and modify and correct the original output content of llama2. We have created our final Alpaca data for fine-tuning,located /dataset/ft_dataset/exp35.json. In addition,exp35 also saves log information of the fine-tuning process.
