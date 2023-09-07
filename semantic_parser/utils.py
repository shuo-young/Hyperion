import os
import pandas as pd


def extract_math(self, loc):
    if os.path.exists(loc) and (os.path.getsize(loc) > 0):
        df = pd.read_csv(loc, header=None, sep='	')
        df.columns = ["a", "b", "res"]
    else:
        df = pd.DataFrame()
    return df
