# Hyperion

## Overview

Artifact repository of work: *<u>Hyperion: Illuminating Shadows of DApp Inconsistencies using LLM and Dataflow-Guided Symbolic Execution</u>*

There are 4 main parts of our artifact:

1. `Helios`: Instruction-tuned model based on LLaMA2 for DApp description analysis. Please go to this directory for a **detailed markdown file**, illustrating the complete **process of our experiments** on the LLM, i.e., *prompt design, prompt segmentation, and instruction-tune.*

2. DApp smart contract analysis:

   - `gigahorse-toolchain`: contains the decompiler and programmed datalog rules in `clients/hyperion.dl`, serving as a bytecode lifter for obtaining contract IR and dataflow information.

   - `symbolic execution`: an IR-based symbolic execution module, using the semantics recovered to guide targeted symbolic execution. The IR-based SE is extensible and programmed with the IR instructions.

   - `semantic_parser`: a semantic recovery module based on dataflow information and graph analysis.

   - `nlp`: a module for extracting key value attributes from `Helios` outputs, based on NLTK.

   - `main.py`: the entrance for contract bytecode analysis, the supported parameters are showing below:

     ```shell
     -dt, --dapp_text: Specify the text information of the tested DApp.
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

3. `DApp_dataset`: dataset used in our experiments, due to the large file limitation of github, we put more than **6GB** data in an anonymous cloud disk. The dataset includes:

   - `risky_DApps`: 54 DApps (descriptions and their corresponding contract code, below the same) labeled when finding DApp inconsistencies. Google cloud link: <https://drive.google.com/drive/folders/1lS8edReFJS41sCN4W0Kuj9sq4Fp2QLdt?usp=drive_link>
   - `wilds`: Crawled DApps for large-scale experiment from DAppBay and DAppRadar. Google cloud link: <https://drive.google.com/drive/folders/1MRj50sYVl1XGBogeL_ETWNYqbIVnEclA?usp=drive_link>
   - `fine-tune`: 63 DApps labeled for instruction-tuning LLaMA2. Google cloud link: <https://drive.google.com/drive/folders/1BDDJNrzBqWR0n5Jkrad33agy2YyappuY?usp=drive_link>
   - `sample_DApp`: as we put our dataset into cloud disk, users can preview our data structure by this directory.
   - `HtmlTextExtractor`: a tool for automatically crawl the website raw text from a given url, serving as a helper.
   - `inconsistency_map.csv`: the mapping csv that shows the problematic DApp with its inconsistency type.

4. `experiment_result`: Our experimental results of `ground truth` and `wild` DApps, please go further into this folder for detailed experiment information:

   - `exec`: scripts used for batch running.
   - `exp_utils`: python scripts for analyzing experimental results.
