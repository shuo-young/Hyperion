from global_params import *

from semantic_parser.graph_analyzer import *
from semantic_parser.decompilation import *
from symbolic_execution.ir_se import *
import six


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
        self.infer_pause = self.decompiler.infer_pause()
        self.storage_way = self.decompiler.get_storage_way()

        self.supply_amount = self.decompiler.get_supply_amount()

        # two phase graph analysis
        log.info("Begin graph analysis...")
        self.fund_transfer_analysis()
        self.state_dependency_analysis()
        self.funcs_to_be_checked = list(
            set(
                self.fund_transfer_graph.unique_funcs
                + self.state_dependency_graph.unique_funcs
            )
        )

        # combination and initialization for targeted SE and double validation & -FPs

    def fund_transfer_analysis(self):
        self.fund_transfer_graph = FundTransferGraph(
            self.sensitive_call, self.call_guarded_by_owner, self.recipient
        )

    def state_dependency_analysis(self):
        # 6 states and 1 storage deduce
        self.state_dependency_graph = StateDependencyGraph(
            self.infer_balance,
            self.infer_time,
            self.infer_supply,
            self.infer_owner,
            self.slot_tainted_by_owner,
            self.infer_pause,
        )

    def get_inputs(self):
        inputs = []
        # first construct cfg
        """Build cfg from ir and perform symbolic execution"""
        logging.info("Building CFG from IR...")
        # get blocks, functions, and tac_block_function from decompiled IR
        blocks, functions, tac_block_function = construct_cfg(self.decompiler.path)
        inputs.append(
            {
                'blocks': blocks,
                'functions': functions,
                'path': self.decompiler.path,
                'tac_block_function': tac_block_function,
                'funcs_to_be_checked': self.funcs_to_be_checked,
                'func_map': self.func_map,
                'fund_transfer_graph': self.fund_transfer_graph,
                'state_dependency_graph': self.state_dependency_graph,
            }
        )
        return inputs
