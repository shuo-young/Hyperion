import pandas as pd
from collections import namedtuple

Transfer = namedtuple('Transfer', ['callStmt', 'recipient', 'amount'])


class FundTransferGraph:
    def __init__(self, sensitive_call_df, call_guarded_by_owner_df, recipient_df):
        # ["callStmt", "recipient", "amount", "funcSign"]
        self.sensitive_call_df = sensitive_call_df
        # ["callStmt", "val", "funcSign"]
        self.call_guarded_by_owner_df = call_guarded_by_owner_df
        # ["callStmt", "to", "funcSign"]
        self.recipient_df = recipient_df
        # 初始化一个字典来保存角色
        self.recipient_role = {}
        self.analyze_transfer()

    def set_role(self):
        guarded_call_slot = {}
        for index, row in self.call_guarded_by_owner_df.iterrows():
            if [row['callStmt']] not in guarded_call_slot.keys():
                guarded_call_slot[row['callStmt']] = [row['val']]
            else:
                guarded_call_slot[row['callStmt']].append(row['val'])
        # first: identify caller or specific address value
        # next: use guarded info to determin the role (user or owner)
        for index, row in self.recipient_df.iterrows():
            if row['to'] == "CALLER" and len(guarded_call_slot[row['callStmt']]) > 0:
                self.recipient_role[row['callStmt']] = "OWNER"
            else:
                self.recipient_role[row['callStmt']] = "NORMAL"
            # self.recipient_role[row['callStmt']] = row['to']

    def analyze_transfer(self):
        funcsign_call = {}
        for index, row in self.sensitive_call_df.iterrows():
            if row["funcSign"] not in funcsign_call.keys():
                funcsign_call[row["funcSign"]] = [
                    Transfer(row['callStmt'], row['recipient'], row['amount'])
                ]
            else:
                funcsign_call[row["funcSign"]].append(
                    Transfer(row['callStmt'], row['recipient'], row['amount'])
                )
        print(funcsign_call)
        self.funcsign_call = funcsign_call
