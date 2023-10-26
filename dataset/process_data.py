import pandas as pd

# 读取Excel文件
excel_file = "data_2.xlsx"  # 替换成你的Excel文件路径
df = pd.read_excel(excel_file)

# 提取需要的两列数据
column1 = "Contract Address"  # 替换成你要提取的第一列的名称
column2 = "Platform"  # 替换成你要提取的第二列的名称
selected_columns = df[[column1, column2]]

# 保存为CSV文件
csv_file = "data.csv"  # 替换成你要保存的CSV文件路径
selected_columns.to_csv(csv_file, index=False, header=False)  # 不保存表头
