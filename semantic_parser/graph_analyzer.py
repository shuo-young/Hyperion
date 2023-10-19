import pandas as pd
from collections import defaultdict, namedtuple
import logging

Transfer = namedtuple('Transfer', ['callStmt', 'recipient', 'amount'])
log = logging.getLogger(__name__)


class FundTransferGraph:
    def __init__(self, sensitive_call_df, clear_call_df):
        # ["callStmt", "recipient", "amount", "funcSign"]
        self.sensitive_call_df = sensitive_call_df
        self.clear_call_df = clear_call_df
        self.calls = {}
        # map ident to calls
        self.clearcall = {}
        # find transfer point (callStmt, recipient, amount)
        self.analyze_transfer()
        self.set_clear_call()

        # actually, we should SE every function with transfer
        self.unique_funcs = list(self.func_call.keys())

    def set_clear_call(self):
        clear_funcSign_callStmt = {}
        # use the decompilation rules to determine
        for _, row in self.clear_call_df.iterrows():
            if row['funcSign'] not in clear_funcSign_callStmt.keys():
                clear_funcSign_callStmt[row['funcSign']] = [row['callStmt']]
            else:
                clear_funcSign_callStmt[row['funcSign']].append(row['callStmt'])

        log.info("clearance call")
        self.clearcall = clear_funcSign_callStmt
        log.info(self.clearcall)

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
            # for finding value of recipient and amount during SE
            self.calls[row['callStmt']] = [row['recipient'], row['amount']]
        log.info("func call")
        log.info(func_call)
        self.func_call = func_call


class StateDependencyGraph:
    def __init__(
        self,
        balance_slot,
        time_slot,
        supply_slot,
        owner_slot,
        slot_tainted_by_owner,
        pause_slot,
        guarded_mint,
    ):
        self.balance_slot = balance_slot
        self.time_slot = time_slot
        self.supply_slot = supply_slot
        self.owner_slot = owner_slot
        self.slot_tainted_by_owner = slot_tainted_by_owner
        self.pause_slot = pause_slot
        self.guarded_mint = guarded_mint

        self.unique_funcs = []
        self.analyze_state_dependency()

    def analyze_state_dependency(self):
        # balance = self.load_df_multimap(self.balance_slot)
        supply = self.load_df_multimap(self.supply_slot)
        time = self.load_df_multimap(self.time_slot)
        pause = self.load_df_multimap(self.pause_slot)
        # slots depends on owner
        # can also be used to judge whether fee depends on the modifiable state variables
        self.slot_dependency_map = self.load_df_map(self.slot_tainted_by_owner)
        self.guarded_mint_map = self.load_df_map(self.guarded_mint, reverse=True)
        log.info("slot dependency map")
        log.info(self.slot_dependency_map)
        log.info("guarded mint map")
        log.info(self.guarded_mint_map)
        # log.info("balance")
        # log.info(balance)
        log.info("supply")
        log.info(supply)
        log.info("time")
        log.info(time)
        log.info("pause")
        log.info(pause)
        # self.balance = balance
        self.supply = supply
        self.time = time
        self.pause = pause
        # self.balance_list = [item for ls in balance.values() for item in ls]
        self.supply_list = [item for ls in supply.values() for item in ls]
        self.time_list = [item for ls in time.values() for item in ls]
        self.pause_list = [item for ls in pause.values() for item in ls]
        merged_dict = defaultdict(lambda: defaultdict(list))
        for d, label in [
            # (balance, 'balance'),
            (supply, 'supply'),
            (time, 'time'),
            (pause, 'pause'),
        ]:
            for key, values in d.items():
                if key not in self.unique_funcs:
                    self.unique_funcs.append(key)
                # merged_dict[key].extend([f"{label}_{value}" for value in values])
                merged_dict[key][label].extend(values)

        log.info(merged_dict)
        self.funcSign_feat_slot_map = merged_dict

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
