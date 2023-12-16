### DApp_dataset

This directory contains the datasets used in the experimental section of the paper. where

- `fine_tune`: A dataset for fine-tuning large models.
- `risky_DAPPs`: A dataset for testing the effectiveness of detection tools. It contains labeled dapps (ground truth).
- `wilds`: A dataset for large-scale experiment. It contains unlabeled dapps (wild).
- `HtmlTextExtractor`: a tool for automatically parsing the website raw text from a given url, serving as a helper.
- `Crawler`: a tool set for crawling wild DApp dataset, i.e., DAppradar crawler, Website crawler, and Contract-crawler, please refer to their readme in each directory.
- `DApp-Collected.xlsx`: DApp collected from DAppradar and DAppbay for finding DApp inconsistencies.
- `inconsistency_map.csv`: the mapping csv that shows the problematic DApp with its inconsistency type.

We have a readme in each dataset directory.

---

Due to the storage limit of Github larget files, we put our DApp datasets to the anonymous google drive.

The 3 datasets' links are follow:

1. risky_DAPPs: <https://drive.google.com/drive/folders/1lS8edReFJS41sCN4W0Kuj9sq4Fp2QLdt?usp=drive_link>

2. wilds: <https://drive.google.com/drive/folders/1MRj50sYVl1XGBogeL_ETWNYqbIVnEclA?usp=drive_link>

3. fine-tune: <https://drive.google.com/drive/folders/1BDDJNrzBqWR0n5Jkrad33agy2YyappuY?usp=drive_link>

For the clarity, we do not name the directory as the inconsistency shown in the paper. For understanding, the mapping relationship is shown below:

```csv=
clear => Unclaimed Fund Flow
fee => Hidden Fee
lock => Adjustable Liquidity
metadata => Volatile NFT Accessibility
pause => Changeable DApp Status
reward => Unguaranteed Reward
supply => Unconstrained Token Supply
```

---

Furthermoe, to illutrate our structure of DApp dataset, we put a sample case in directory `sample`.
