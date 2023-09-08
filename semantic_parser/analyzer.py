import pandas as pd


class FundTransferGraph:
    def __init__(self):
        # 初始化一个DataFrame来保存转账记录
        self.transfers = pd.DataFrame(
            columns=['callStmt', 'sender', 'receiver', 'amount', 'funcSign']
        )
        # 初始化一个字典来保存角色
        self.roles = {}

    def set_role(self, address: str, role: str):
        self.roles[address] = role

    def get_role(self, address: str):
        return self.roles.get(address, None)

    def add_transfer(self, transfer_row: pd.Series):
        # 直接将DataFrame的一行添加到transfers
        self.transfers = self.transfers.append(transfer_row, ignore_index=True)

    def get_all_transfers(self):
        # 返回所有转账记录
        return self.transfers
