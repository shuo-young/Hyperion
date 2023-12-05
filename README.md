# Hyperion

## Overview

*<u>Detecting DApp Inconsistencies using LLM and Dataflow-guided Symbolic Execution</u>*

There are 4 main parts of our artifact

1. LLM for DApp description analysis: `llama2_finetuned_for_Dapp_inconsistency`, please go to this directory for a **detailed markdown file**, illustrating the complete **process of our experiments** on the LLM, i.e., *prompt design, token split, and fine-tune.*
2. DApp smart contract analysis: `hyperion_core`
3. Dataset for *fine-tune, ground truth* for defining inconsistencies with a mapping csv that shows the problematic DApp with its inconsistency type, and *wild DApps* collected from DAppBay and DAppRadar: `dataset`
4. Dataset of our experimental results of ground truth and wild DApps: `experiment_result`

## Structure

1. `dataset`: contains dataset for running ground truth and wild cases.
2. `gigahorse-toolchain`: contains the decompiler and programmed datalog rules in `clients/hyperion.dl`, serving as a bytecode lifter for obtaining contract IR and dataflow information.
3. `semantic_parser`: a semantic recovery module based on dataflow information and graph analysis.
4. `symbolic_execution`: a IR-based symbolic execution module, using the semantics recovered to guide targeted symbolic execution. The IR-based SE is extensible and programmed with the IR instructions.
5. `nlp`: a module for extracting key value attributes from LLM outputs, based on NLTK.
6. `exec`: scripts used for batch running.
7. `exp_utils`: python scripts for analyzing experimental results.
