import pandas as pd
from collections import defaultdict, namedtuple
import logging

Transfer = namedtuple('Transfer', ['callStmt', 'recipient', 'amount', 'type'])
log = logging.getLogger(__name__)


class IRSE_Checker:
    def __init__(self, funcSign):
        self.funcSign = funcSign

    def set_transfer_checker(self, transfer_checker):
        self.transfer_checker = transfer_checker


# todo: link recipient role to the specific function
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
        # map ident to calls
        self.calls = {}
        self.funcSign_to_transfer = {}
        # find transfer point (callStmt, recipient, amount)
        self.analyze_transfer()

        # actually, we should SE every function with transfer
        self.unique_funcs = list(self.func_call.keys())

    def set_role(self):
        funcSign_call_recipient = {}
        funcSign_guarded_call = {}
        for _, row in self.sensitive_call_df.iterrows():
            funcSign_call_recipient[row["funcSign"]] = {}
        for _, row in self.call_guarded_by_owner_df.iterrows():
            if row["funcSign"] not in funcSign_guarded_call.keys():
                funcSign_guarded_call[row["funcSign"]] = [row['callStmt']]
            else:
                funcSign_guarded_call[row["funcSign"]].append(row['callStmt'])
        # first: identify caller or specific address value
        # next: use guarded info to determine the role (user or owner)
        for _, row in self.recipient_df.iterrows():
            # roi or clear type
            if row['to'] == "CALLER":
                if row["funcSign"] in funcSign_guarded_call.keys():
                    if row['callStmt'] in funcSign_guarded_call[row["funcSign"]]:
                        # msg.sender.transfer(), msg.sender = owner
                        funcSign_call_recipient[row["funcSign"]][
                            row['callStmt']
                        ] = "OWNER"
                else:
                    funcSign_call_recipient[row["funcSign"]][row['callStmt']] = "USER"
            elif row['to'] == "FUNARG":
                funcSign_call_recipient[row["funcSign"]][row['callStmt']] = "FUNARG"
            else:
                # normal can be the tax receiver address
                funcSign_call_recipient[row["funcSign"]][row['callStmt']] = "KNOWN"
        self.recipient_role = funcSign_call_recipient
        log.info("recipient role")
        log.info(self.recipient_role)

    def analyze_transfer(self):
        self.set_role()
        func_call = {}
        for _, row in self.sensitive_call_df.iterrows():
            if row['callStmt'] in self.recipient_role[row["funcSign"]].keys():
                type = self.recipient_role[row["funcSign"]][row['callStmt']]
            else:
                type = "UNKNOWN"
            if row["funcSign"] not in func_call.keys():
                func_call[row["funcSign"]] = [
                    Transfer(row['callStmt'], row['recipient'], row['amount'], type)
                ]
            else:
                func_call[row["funcSign"]].append(
                    Transfer(row['callStmt'], row['recipient'], row['amount'], type)
                )
            # for finding value of recipient and amount during SE
            self.calls[row['callStmt']] = [row['recipient'], row['amount'], type]

        self.funcSign_to_transfer = func_call

        log.info("func call")
        log.info(self.funcSign_to_transfer)
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
    ):
        self.funcSign_to_state = {}
        self.balance_slot = balance_slot
        self.time_slot = time_slot
        self.supply_slot = supply_slot
        self.owner_slot = owner_slot
        self.slot_tainted_by_owner = slot_tainted_by_owner
        self.pause_slot = pause_slot

        self.unique_funcs = []
        self.analyze_state_dependency()
        log.info("funcs to be tested")
        log.info(self.unique_funcs)

    def analyze_state_dependency(self):
        balance = self.load_df_multimap(self.balance_slot)
        supply = self.load_df_multimap(self.supply_slot)
        time = self.load_df_multimap(self.time_slot)
        pause = self.load_df_multimap(self.pause_slot)
        # slot dependant on owner
        self.slot_dependency_map = self.load_df_map(self.slot_tainted_by_owner)
        log.info("slot dependency map")
        log.info(self.slot_dependency_map)
        log.info("balance")
        log.info(balance)
        log.info("supply")
        log.info(supply)
        log.info("time")
        log.info(time)
        log.info("pause")
        log.info(pause)
        self.balance = balance
        self.supply = supply
        self.time = time
        self.pause = pause
        self.balance_list = [item for ls in balance.values() for item in ls]
        self.supply_list = [item for ls in supply.values() for item in ls]
        self.time_list = [item for ls in time.values() for item in ls]
        self.pause_list = [item for ls in pause.values() for item in ls]
        merged_dict = defaultdict(lambda: defaultdict(list))
        for d, label in [
            (balance, 'balance'),
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
