# Hyperion

## Overview

Artifact repository of the work: *<u>Hyperion: Illuminating Shadows of DApp Inconsistencies using LLM and Dataflow-Guided Symbolic Execution</u>*

There are 4 main parts of our artifact:

1. `HyperText`: Instruction-tuned model based on LLaMA2 for DApp description analysis. Please go to this directory for a **detailed markdown file**, illustrating the complete **process of our experiments** on the LLM, i.e., *prompt design, prompt segmentation, and instruction-tune.*

2. `HyperCode`: DApp smart contract analysis:

   - `gigahorse-toolchain`: contains the decompiler and programmed datalog rules in `clients/hyperion.dl`, serving as a bytecode lifter for obtaining contract IR and dataflow information.

   - `symbolic execution`: an IR-based symbolic execution module, using the semantics recovered to guide targeted symbolic execution. The IR-based SE is extensible and programmed with the IR instructions.
      - `ir_basic_blocks`: constructing basic blocks and functions from decompiled contract IR.

      - `ir_se`: extensible symbolic engine on contract IR, encompassing IR-instruction rules.

      - `state_extractor`: on-chain data fetcher for checking attributes, e.g., programmed fee ratio.

      - `vargenerator`: classic generator for symbolic variables.

      - `utils`: some utility methods during symbolic execution.

   - `semantic_parser`: a semantic recovery module based on dataflow information and graph analysis.
      - `semantic`: main class for preparing recovered semantics from dataflow analysis and graph analysis.

      - `decompilation`: decompiler dispatcher and information collector for graph analysis.

      - `graph_analyzer`: connector that assembles dataflow information to prepare function-level information for directed symbolic execution.

   - `nlp`: a module for extracting key value attributes from `HyperText` outputs, based on NLTK.

   - `main.py`: the entrance for contract bytecode analysis, the supported parameters are showing below:

     ```shell
     -a, --address: Enter the contract address of the DApp.
     -bp, --blockchain_platform: Define the blockchain platform where the DApp contract is deployed (default: "ETH").
      including: 
         1. ETH
         2. Polygon
         3. Cronos
         4. Avalanche
         5. Fantom
         6. Moonbeam
         7. Arbitrum
         8. Tron
         9. Optimism
         10. Moonriver
         11. SKALE
         12. Base
         13. BSC
     -bn, --block_number: Set the tested blockchain snapshot.
     -v, --verbose: Enable verbose output for detailed logging.
     -n, --name: Name of the DApp.
     -d, --directory: Path to the output directory (default: "result").
     ```

   - `global_params.py`: the global parameter settings for contract bytecode analysis.

3. `DApp_dataset`: dataset used in our experiments, due to the large file limitation of Github, we put more than **6GB** data in an anonymous cloud disk. The dataset includes:

   - `risky_DApps`: Ground Truth DApps (descriptions and their corresponding contract code, below the same) labeled when finding DApp inconsistencies. Google cloud link: <https://drive.google.com/drive/folders/1lS8edReFJS41sCN4W0Kuj9sq4Fp2QLdt?usp=drive_link>

   - `wilds`: Crawled DApps for large-scale experiment from DAppBay and DAppRadar. Google cloud link: <https://drive.google.com/drive/folders/1MRj50sYVl1XGBogeL_ETWNYqbIVnEclA?usp=drive_link>

   - `fine-tune`: DApps labeled for instruction-tuning LLaMA2. Google cloud link: <https://drive.google.com/drive/folders/1BDDJNrzBqWR0n5Jkrad33agy2YyappuY?usp=drive_link>

   - `sample_DApp`: as we put our dataset into cloud disk, users can preview our data structure by this directory.
      - Website source package (as many risky DApps are ''unavailable'' which just exist for a while).
      - Contract code.

   - `HtmlTextExtractor`: a tool for automatically parsing the website raw text from a given url, serving as a helper.

   - `Crawler`: a toolset for crawling wild DApp dataset, i.e., DAppradar crawler, Website crawler, and Contract-crawler.

   - `DApp-Collected.xlsx`: DApp collected from DAppradar and DAppbay for finding DApp inconsistencies.

   - `inconsistency_map.csv`: the mapping csv that shows the problematic DApp with its inconsistency type.

4. `experiment_result`: Our experimental results of `ground truth` and `wild` DApps, please go further into this folder for detailed experiment information:
   - `dataset`: csv data that records (DApp's name, DApp contract address, blockchain platform), including ground truth and wild datasets.

   - `ground_truth`: the running output on ground truth dataset.

   - `wild`: the running output on wild dataset

### Some other Utils

- `exec`: shell scripts used for batch running.
- `exp_utils`: python scripts for analyzing experimental results.
