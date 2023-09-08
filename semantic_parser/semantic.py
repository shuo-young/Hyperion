import os
from global_params import *
import pandas as pd

from semantic_parser.graph_analyzer import *
from semantic_parser.decompilation import *
from ir_se import *


class TargetedParameters:
    def __init__(self, **kwargs):
        attr_defaults = {"targeted_funcsign": '', "path": '', "targeted_block": None}
        for attr, default in six.iteritems(attr_defaults):
            setattr(self, attr, kwargs.get(attr, default))

    def copy(self):
        _kwargs = custom_deepcopy(self.__dict__)
        return Parameter(**_kwargs)


class Semantics:
    def __init__(self, platform, address, block_number):
        self.decompiler = Decompiler(platform, address, block_number)
        self.recipient = self.decompiler.get_recipient()
        self.call_guarded_by_owner = self.decompiler.get_call_guarded_info()
        self.sensitive_call = self.decompiler.get_sensitive_call()
        self.slot_tainted_by_owner = self.decompiler.get_slot_tainted_by_owner()

        self.func_map = self.decompiler.func_map

        self.infer_balance = self.decompiler.infer_balance()
        self.infer_time = self.decompiler.infer_time()
        self.infer_supply = self.decompiler.infer_supply()
        self.infer_owner = self.decompiler.infer_owner()

    def fund_transfer_analysis(self):
        fund_transfer_graph = FundTransferGraph(
            self.sensitive_call, self.call_guarded_by_owner, self.recipient
        )
        funcsign_call = fund_transfer_graph.funcsign_call

        global targeted_params
        path = "./gigahorse-toolchain/.temp/eth_bnbpirates/out/"
        targeted_params = TargetedParameters(
            targeted_funcsign=self.func_map["0x3955f0fe"], path=path
        )
        run_build_cfg_and_analyze(targeted_params)
