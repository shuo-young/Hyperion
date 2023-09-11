import pandas as pd
from collections import defaultdict, namedtuple

Transfer = namedtuple('Transfer', ['callStmt', 'recipient', 'amount'])


class FundTransferGraph:
    def __init__(self, sensitive_call_df, call_guarded_by_owner_df, recipient_df):
        # ["callStmt", "recipient", "amount", "funcSign"]
        self.sensitive_call_df = sensitive_call_df
        # ["callStmt", "val", "funcSign"]
        self.call_guarded_by_owner_df = call_guarded_by_owner_df
        # ["callStmt", "to", "funcSign"]
        self.recipient_df = recipient_df
        # initialize for role mapping
        self.recipient_role = {}
        # find transfer point (callStmt, recipient, amount)
        self.analyze_transfer()
        self.set_role()
        # actually, we should SE every function with transfer
        self.unique_funcs = list(self.func_call.keys())
        print(self.unique_funcs)

    def set_role(self):
        guarded_call_slot = {}
        for _, row in self.call_guarded_by_owner_df.iterrows():
            if row['callStmt'] not in guarded_call_slot.keys():
                guarded_call_slot[row['callStmt']] = [row['val']]
            else:
                guarded_call_slot[row['callStmt']].append(row['val'])
        # first: identify caller or specific address value
        # next: use guarded info to determin the role (user or owner)
        for _, row in self.recipient_df.iterrows():
            if row['to'] == "CALLER" and len(guarded_call_slot[row['callStmt']]) > 0:
                self.recipient_role[row['callStmt']] = "OWNER"
            else:
                self.recipient_role[row['callStmt']] = "NORMAL"
        print(self.recipient_role)

    def analyze_transfer(self):
        func_call = {}
        for _, row in self.sensitive_call_df.iterrows():
            if row["funcSign"] not in func_call.keys():
                func_call[row["funcSign"]] = [
                    Transfer(row['callStmt'], row['recipient'], row['amount'])
                ]
            else:
                func_call[row["funcSign"]].append(
                    Transfer(row['callStmt'], row['recipient'], row['amount'])
                )
        print(func_call)
        self.func_call = func_call


class StateDependencyGraph:
    def __init__(
        self, balance_slot, time_slot, supply_slot, owner_slot, slot_tainted_by_owner
    ):
        self.balance_slot = balance_slot
        self.time_slot = time_slot
        self.supply_slot = supply_slot
        self.owner_slot = owner_slot
        self.slot_tainted_by_owner = slot_tainted_by_owner

        self.unique_funcs = []
        self.analyze_state_dependency()

        print(self.unique_funcs)

    def analyze_state_dependency(self):
        balance = self.load_df_multimap(self.balance_slot)
        supply = self.load_df_multimap(self.supply_slot)
        time = self.load_df_multimap(self.time_slot)
        # slot depended by owner
        self.slot_dependency_map = self.load_df_map(self.slot_tainted_by_owner)
        print(self.slot_dependency_map)
        print(balance)
        print(supply)
        print(time)
        merged_dict = defaultdict(lambda: defaultdict(list))
        for d, label in [
            (balance, 'balance'),
            (supply, 'supply'),
            (time, 'time'),
        ]:
            for key, values in d.items():
                if key not in self.unique_funcs:
                    self.unique_funcs.append(key)
                # merged_dict[key].extend([f"{label}_{value}" for value in values])
                merged_dict[key][label].extend(values)

        print(merged_dict)
        self.funcSign_feat_slot_map = merged_dict

        # maybe for the pic draw
        # G = nx.DiGraph()
        # for funcSign, details in merged_dict.items():
        #     for key, slots in details.items():
        #         for slot in slots:
        #             G.add_edge(funcSign, slot, label=key)

        # for _, row in self.slot_tainted_by_owner.iterrows():
        #     G.add_edge(row['owner'], row['slot'], label=row['funcSign'])

        # pos = nx.spring_layout(G)  # 使用spring布局
        # nx.draw_networkx_nodes(G, pos)
        # nx.draw_networkx_edges(G, pos)
        # nx.draw_networkx_labels(G, pos)
        # plt.title("Slots and Function Signatures Dependency Graph")
        # # plt.show()
        # plt.savefig("image.png")

    def load_df_multimap(self, df):
        ret = defaultdict(list)
        for _, row in df.iterrows():
            ret[row[1]].append(row[0])
        return ret

    def load_df_map(self, df, reverse: bool = False):
        return (
            {row[1]: row[0] for _, row in df.iterrows()}
            if reverse
            else {row[0]: row[1] for _, row in df.iterrows()}
        )