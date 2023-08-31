from ir_basic_blocks import *
from z3 import *
from symbolic_execution.semantic_analysis import *
from symbolic_execution.vargenerator import *


class Parameter:
    def __init__(self, **kwargs):
        attr_defaults = {
            "stack": [],
            "calls": [],
            "memory": [],
            "visited": [],
            "overflow_pcs": [],
            "mem": {},
            "analysis": {},
            "sha3_list": {},
            "global_state": {},
            "path_conditions_and_vars": {},
        }
        for attr, default in six.iteritems(attr_defaults):
            setattr(self, attr, kwargs.get(attr, default))

    def copy(self):
        _kwargs = custom_deepcopy(self.__dict__)
        return Parameter(**_kwargs)


def get_init_global_state(path_conditions_and_vars):
    global_state = {"balance": {}, "pc": 0}
    init_is = (
        init_ia
    ) = (
        deposited_value
    ) = (
        sender_address
    ) = (
        receiver_address
    ) = (
        gas_price
    ) = (
        origin
    ) = (
        currentCoinbase
    ) = (
        currentNumber
    ) = (
        currentDifficulty
    ) = (
        currentGasLimit
    ) = currentChainId = currentSelfBalance = currentBaseFee = callData = None

    sender_address = BitVec("Is", 256)
    receiver_address = BitVec("Ia", 256)
    deposited_value = BitVec("Iv", 256)
    init_is = BitVec("init_Is", 256)
    init_ia = BitVec("init_Ia", 256)

    path_conditions_and_vars["Is"] = sender_address
    path_conditions_and_vars["Ia"] = receiver_address
    path_conditions_and_vars["Iv"] = deposited_value

    # from s to a, s is sender, a is receiver
    # v is the amount of ether deposited and transferred
    constraint = deposited_value >= BitVecVal(0, 256)
    path_conditions_and_vars["path_condition"].append(constraint)
    constraint = init_is >= deposited_value
    path_conditions_and_vars["path_condition"].append(constraint)
    constraint = init_ia >= BitVecVal(0, 256)
    path_conditions_and_vars["path_condition"].append(constraint)

    # update the balances of the "caller" and "callee"re
    global_state["balance"]["Is"] = init_is - deposited_value
    global_state["balance"]["Ia"] = init_ia + deposited_value

    if not gas_price:
        new_var_name = gen.gen_gas_price_var()
        gas_price = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = gas_price

    if not origin:
        new_var_name = gen.gen_origin_var()
        origin = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = origin

    if not currentCoinbase:
        new_var_name = "IH_c"
        currentCoinbase = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = currentCoinbase

    if not currentNumber:
        new_var_name = "IH_i"
        currentNumber = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = currentNumber

    if not currentDifficulty:
        new_var_name = "IH_d"
        currentDifficulty = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = currentDifficulty

    if not currentGasLimit:
        new_var_name = "IH_l"
        currentGasLimit = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = currentGasLimit

    if not currentChainId:
        new_var_name = "IH_cid"
        currentChainId = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = currentChainId

    if not currentSelfBalance:
        new_var_name = "IH_b"
        currentSelfBalance = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = currentSelfBalance

    if not currentBaseFee:
        new_var_name = "IH_f"
        currentBaseFee = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = currentBaseFee

    new_var_name = "IH_s"
    currentTimestamp = BitVec(new_var_name, 256)
    path_conditions_and_vars[new_var_name] = currentTimestamp

    # the state of the current contract
    if "Ia" not in global_state:
        global_state["Ia"] = {}
    global_state["miu_i"] = 0
    global_state["value"] = deposited_value
    global_state["sender_address"] = sender_address
    global_state["receiver_address"] = receiver_address
    global_state["gas_price"] = gas_price
    global_state["origin"] = origin
    global_state["currentCoinbase"] = currentCoinbase
    global_state["currentTimestamp"] = currentTimestamp
    global_state["currentNumber"] = currentNumber
    global_state["currentDifficulty"] = currentDifficulty
    global_state["currentGasLimit"] = currentGasLimit

    global_state["currentChainId"] = currentChainId
    global_state["currentSelfBalance"] = currentSelfBalance
    global_state["currentBaseFee"] = currentBaseFee

    return global_state


def initGlobalVars():
    # Initialize global variables
    global solver
    # Z3 solver
    solver = Solver()
    solver.set("timeout", global_params.TIMEOUT)

    global MSIZE
    MSIZE = False

    global revertible_overflow_pcs
    revertible_overflow_pcs = set()

    global g_timeout
    g_timeout = False

    global visited_pcs
    visited_pcs = set()

    global results
    global start_block_to_func_sig
    start_block_to_func_sig = {}

    results = {
        "evm_code_coverage": "",
        "instructions": "",
        "time": "",
        "analysis": {},
    }

    global calls_affect_state
    calls_affect_state = {}

    # capturing the last statement of each basic block
    global end_ins_dict
    end_ins_dict = {}

    # capturing all the instructions, keys are corresponding addresses
    global instructions
    instructions = {}

    # capturing the "jump type" of each basic block
    global jump_type
    jump_type = {}

    global vertices
    vertices = {}

    global edges
    edges = {}

    # start: end
    # global blocks
    # blocks = {}

    global visited_edges
    visited_edges = {}

    global money_flow_all_paths
    money_flow_all_paths = []

    global reentrancy_all_paths
    reentrancy_all_paths = []

    # store the path condition corresponding to each path in money_flow_all_paths
    global path_conditions
    path_conditions = []

    global global_problematic_pcs  # for different defects
    global_problematic_pcs = {
        "integer_underflow": [],
        "integer_overflow": [],
    }

    # store global variables, e.g. storage, balance of all paths
    global all_gs
    all_gs = []

    global total_no_of_paths
    total_no_of_paths = 0

    global no_of_test_cases
    no_of_test_cases = 0

    # to generate names for symbolic variables
    global gen
    gen = Generator()


def run_build_cfg_and_analyze(path):
    initGlobalVars()
    build_cfg_and_analyze(path)


def build_cfg_and_analyze(path):
    """Build cfg from ir and perform symbolic execution"""
    logging.info("Building CFG from IR...")
    global blocks
    blocks, functions = construct_cfg(path)
    print(blocks.keys())
    # for block in blocks.values():
    # print(block)
    # print(block.statements)
    print(functions["0x0"].head_block.statements)
    targeted_sym_exec()


def targeted_sym_exec():
    # executing, starting from beginning
    path_conditions_and_vars = {"path_condition": []}
    global_state = get_init_global_state(path_conditions_and_vars)
    analysis = init_analysis()
    params = Parameter(
        path_conditions_and_vars=path_conditions_and_vars,
        global_state=global_state,
        analysis=analysis,
    )
    # if g_src_map:
    # start_block_to_func_sig = get_start_block_to_func_sig()
    # print(start_block_to_func_sig)

    return sym_exec_block(params, blocks["0x210"], blocks["0x0"], 0, -1, "fallback")


def sym_exec_block(params, block, pre_block, depth, func_call, current_func_name):
    global solver
    global visited_edges
    global path_conditions
    global global_problematic_pcs
    global all_gs
    global results

    visited = params.visited
    stack = params.stack
    mem = params.mem
    memory = params.memory
    global_state = params.global_state
    sha3_list = params.sha3_list
    path_conditions_and_vars = params.path_conditions_and_vars
    analysis = params.analysis
    calls = params.calls

    # print(block)
    # statement[1] = op
    for statement in block.statements:
        sym_exec_ins(params, block, statement[1], func_call, current_func_name)
    successors = block.successors
    for successor in successors:
        new_params = params.copy()
        sym_exec_block(
            new_params, successor, block, depth, func_call, current_func_name
        )


def sym_exec_ins(params, block, instr, func_call, current_func_name):
    global MSIZE
    global visited_pcs
    global solver
    global vertices
    global edges
    global blocks
    global calls_affect_state
    global instructions

    stack = params.stack
    mem = params.mem
    memory = params.memory
    global_state = params.global_state
    sha3_list = params.sha3_list
    path_conditions_and_vars = params.path_conditions_and_vars
    analysis = params.analysis
    calls = params.calls
    # overflow_pcs = params.overflow_pcs

    visited_pcs.add(global_state["pc"])

    instr_parts = str.split(instr, " ")
    opcode = instr_parts[0]

    if opcode == "INVALID":
        return
    elif opcode == "ASSERTFAIL":
        return

    # collecting the analysis result by calling this skeletal function
    # this should be done before symbolically executing the instruction,
    # since SE will modify the stack and mem

    log.debug("==============================")
    log.debug("EXECUTING: " + instr)
    print(block.ident)
    print(instr)


if __name__ == "__main__":
    path = "../gigahorse-toolchain/.temp/eth_bnbpirates/out/"
    run_build_cfg_and_analyze(path)
