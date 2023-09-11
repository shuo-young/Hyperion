import os
from global_params import *
import pandas as pd

from semantic_parser.graph_analyzer import *
from semantic_parser.decompilation import *
from ir_se import *


class TargetedParameters:
    def __init__(self, **kwargs):
        attr_defaults = {
            # target func sign
            "funcSign": '',
            "path": '',
            "target_func": '',
            "target_block": None,
            "fund_transfer_info": None,
            "state_dependency_info": None,
        }
        for attr, default in six.iteritems(attr_defaults):
            setattr(self, attr, kwargs.get(attr, default))

    def copy(self):
        _kwargs = custom_deepcopy(self.__dict__)
        return TargetedParameters(**_kwargs)


class Semantics:
    def __init__(self, platform, address, block_number):
        self.address = address
        self.decompiler = Decompiler(platform, address, block_number)
        self.recipient = self.decompiler.get_recipient()
        self.call_guarded_by_owner = self.decompiler.get_call_guarded_info()
        self.sensitive_call = self.decompiler.get_sensitive_call()

        # func selector to its id
        self.func_map = self.decompiler.func_map
        # get slots info
        self.infer_balance = self.decompiler.infer_balance()
        self.infer_time = self.decompiler.infer_time()
        self.infer_supply = self.decompiler.infer_supply()
        self.infer_owner = self.decompiler.infer_owner()
        self.slot_tainted_by_owner = self.decompiler.get_slot_tainted_by_owner()

        # two phase graph analysis
        self.fund_transfer_analysis()
        self.state_dependency_analysis()
        self.funcs_to_be_checked = list(
            set(
                self.fund_transfer_graph.unique_funcs
                + self.state_dependency_graph.unique_funcs
            )
        )

        # combination and initialization for targeted SE and double validation & -FPs
        self.analyze()

    def fund_transfer_analysis(self):
        self.fund_transfer_graph = FundTransferGraph(
            self.sensitive_call, self.call_guarded_by_owner, self.recipient
        )

    def state_dependency_analysis(self):
        self.state_dependency_graph = StateDependencyGraph(
            self.infer_balance,
            self.infer_time,
            self.infer_supply,
            self.infer_owner,
            self.slot_tainted_by_owner,
        )

    def analyze(self):
        # """Build cfg from ir and perform symbolic execution"""
        # logging.info("Building CFG from IR...")
        # got the ir data structure path for CFG
        path = "./gigahorse-toolchain/.temp/" + self.address + "/out/"

        # init params for target SE
        # should note: target functions (head blocks), critical slots and dependency relationship
        for funcSign in self.funcs_to_be_checked:
            target_params = TargetedParameters(
                path=path,
                funcSign=funcSign,
                target_func=self.func_map[funcSign],
                fund_transfer_info=self.fund_transfer_graph,
                state_dependency_info=self.state_dependency_graph,
            )
            run_build_cfg_and_analyze(target_params)
            print("======================END=====================")

        # could be parallel for multithread SE process
        # run_build_cfg_and_analyze(target_params)
