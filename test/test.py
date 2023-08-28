import pandas as pd


address = "bnbpirates_mod"
add_loc = "./gigahorse-toolchain/.temp/" + address + "/out/Hyperion_Add.csv"
# sub
sub_loc = "./gigahorse-toolchain/.temp/" + address + "/out/Hyperion_Sub.csv"

# mul
mul_loc = "./gigahorse-toolchain/.temp/" + address + "/out/Hyperion_Mul.csv"

# div
div_loc = "./gigahorse-toolchain/.temp/" + address + "/out/Hyperion_Div.csv"

import pandas as pd

# 读取可能流向sink site的变量
sink_df = pd.read_csv(
    "./gigahorse-toolchain/.temp/"
    + "bnbpirates_mod"
    + "/out/Hyperion_TransferETHAmountToCaller.csv",
    header=None,
    sep='	',
)
# print(sink_df)
start_vars = sink_df.iloc[:, 3].tolist()  # 假设可能流向sink site的变量位于第四列

# 读取所有的运算操作csv
add_df = pd.read_csv(add_loc, header=None, sep='	')
sub_df = pd.read_csv(sub_loc, header=None, sep='	')
mul_df = pd.read_csv(mul_loc, header=None, sep='	')
div_df = pd.read_csv(div_loc, header=None, sep='	')

# 将所有的运算数据框合并到一个列表中
operations = [("+", add_df), ("-", sub_df), ("*", mul_df), ("/", div_df)]


def trace_forward(var, path=[]):
    results = []
    for op, df in operations:
        for _, row in df[(df[0] == var) | (df[1] == var)].iterrows():
            c = row[2]
            new_path = path + [(row[0], op, row[1], c)]
            results.extend(trace_forward(c, new_path))
    if not results:
        return [path]
    return results


all_paths = []
for var in start_vars:
    all_paths.extend(trace_forward(var))

# 打印所有的路径
for path in all_paths:
    print(" -> ".join(["{} {} {} = {}".format(a, op, b, c) for a, op, b, c in path]))
