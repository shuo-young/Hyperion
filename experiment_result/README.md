### experiment_result

This directory contains the raw experimental output of our evaluation section. Details about folders:

- `dataset`: csv data that records (DApp's name, DApp contract address, blockchain platform), including ground truth and wild datasets.

- `ground_truth`: the running output on ground truth dataset.

  - `backend`: the running output of contract bytecode analysis.

  - `frontend`: the running output of description analysis.

  - `evaluation_gt`: the inconsistency detection results of each DApp.

  - `exp_category_gt`: the catogrized detection result according to the inconsistency type. For the clarity, we do not use the name shown in the paper. The mapping relationship is shown below:

    ```csv
    clear => Unclaimed Fund Flow
    fee => Hidden Fee
    lock => Adjustable Liquidity
    metadata => Volatile NFT Accessibility
    pause => Changeable DApp Status
    reward => Unguaranteed Reward
    supply => Unconstrained Token Supply
    ```

- `wild`: the running output on wild dataset

  - `backend`: the running output of contract bytecode analysis on wild DApps.
  - `frontend`: the running output of description analysis on wild DApps.
  - `evaluation_wild`: the inconsistency detection results of each wild DApp.
  - `exp_category_wild`: the catogrized wild detection result according to the inconsistency type.
  - `sampling_exp`: sampling experiment based on the interval 10 and a confidence of 95%.

### FN and FP analysis details

Our paper only highlights some critical information of our analysis on the FNs and FPs due to the page limit. We now use this repo to illutrate the details of them.
