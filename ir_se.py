from ir_basic_blocks import *
from z3 import *
from symbolic_execution.semantic_analysis import *
from symbolic_execution.vargenerator import *
from symbolic_execution.execution_states import (
    UNKNOWN_INSTRUCTION,
    EXCEPTION,
    PICKLE_PATH,
)
from symbolic_execution.vargenerator import *
from symbolic_execution.utils import *
import zlib
import base64
from numpy import mod

log = logging.getLogger(__name__)

# Store visited blocks
visited_blocks = set()

UNSIGNED_BOUND_NUMBER = 2**256 - 1
CONSTANT_ONES_159 = BitVecVal((1 << 160) - 1, 256)

Assertion = namedtuple('Assertion', ['pc', 'model'])
Underflow = namedtuple('Underflow', ['pc', 'model'])
Overflow = namedtuple('Overflow', ['pc', 'model'])


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

    global env_dict
    env_dict = {}

    global var_to_source
    var_to_source = {}


def run_build_cfg_and_analyze():
    initGlobalVars()
    build_cfg_and_analyze()


def build_cfg_and_analyze():
    """Build cfg from ir and perform symbolic execution"""
    logging.info("Building CFG from IR...")
    global blocks
    blocks, functions = construct_cfg(path)
    # todo need label jump type and mark vertice

    # print(blocks.keys())
    # for block in blocks.values():
    # print(block)
    # print(block.statements)
    # print(functions["0x0"].head_block.statements)
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
    print("--------------------")
    print(block.ident)

    visited = params.visited
    stack = params.stack
    mem = params.mem
    memory = params.memory
    global_state = params.global_state
    sha3_list = params.sha3_list
    path_conditions_and_vars = params.path_conditions_and_vars
    analysis = params.analysis
    calls = params.calls

    Edge = namedtuple("Edge", ["v1", "v2"])

    current_edge = Edge(pre_block, block)
    if current_edge in visited_edges:
        updated_count_number = visited_edges[current_edge] + 1
        visited_edges.update({current_edge: updated_count_number})
    else:
        visited_edges.update({current_edge: 1})

    if visited_edges[current_edge] > global_params.LOOP_LIMIT:
        log.debug("Overcome a number of loop limit. Terminating this path ...")
        return stack

    # print(block)
    # statement[1] = op
    for statement in block.statements:
        # 'Statement', ['ident', 'op', 'operands', 'defs']
        sym_exec_ins(params, block, statement, func_call, current_func_name)

    visited.append(block)
    depth += 1

    # successors can only be 0 or 1 or 2 or 3
    # CALLPRIVATE opcode can insert the successors to make it 3
    successors = block.successors

    if len(successors) == 2:
        # conditional jump
        branch_expression = block.get_branch_expression()
        solver.push()  # SET A BOUNDARY FOR SOLVER
        solver.add(branch_expression)

        try:
            if solver.check() == unsat:
                log.debug("INFEASIBLE PATH DETECTED")
            else:
                left_branch = block.successors[1]
                new_params = params.copy()
                # new_params.global_state["pc"] = left_branch
                new_params.path_conditions_and_vars["path_condition"].append(
                    branch_expression
                )
                last_idx = (
                    len(new_params.path_conditions_and_vars["path_condition"]) - 1
                )
                sym_exec_block(
                    new_params, left_branch, block, depth, func_call, current_func_name
                )
        except TimeoutError:
            raise
        except Exception as e:
            print(e)

        solver.pop()  # POP SOLVER CONTEXT

        solver.push()  # SET A BOUNDARY FOR SOLVER
        negated_branch_expression = Not(branch_expression)
        solver.add(negated_branch_expression)

        log.debug("Negated branch expression: " + str(negated_branch_expression))

        try:
            if solver.check() == unsat:
                # Note that this check can be optimized. I.e. if the previous check succeeds,
                # no need to check for the negated condition, but we can immediately go into
                # the else branch
                log.debug("INFEASIBLE PATH DETECTED")
            else:
                right_branch = block.successors[0]
                new_params = params.copy()
                # new_params.global_state["pc"] = right_branch
                new_params.path_conditions_and_vars["path_condition"].append(
                    negated_branch_expression
                )
                last_idx = (
                    len(new_params.path_conditions_and_vars["path_condition"]) - 1
                )
                sym_exec_block(
                    new_params, right_branch, block, depth, func_call, current_func_name
                )
        except TimeoutError:
            raise
        except Exception as e:
            print(e)
        solver.pop()  # POP SOLVER CONTEXT
        updated_count_number = visited_edges[current_edge] - 1
        visited_edges.update({current_edge: updated_count_number})
    # for successor in successors:
    #     new_params = params.copy()
    #     sym_exec_block(
    #         new_params, successor, block, depth + 1, func_call, current_func_name
    #     )

    elif len(successors) == 1:
        # unconditional jump opcode
        successor = block.successors[0]
        new_params = params.copy()
        # new_params.global_state["pc"] = successor
        sym_exec_block(
            new_params, successor, block, depth, func_call, current_func_name
        )
    elif len(successors) == 0 or depth > global_params.DEPTH_LIMIT:
        pass
    else:
        updated_count_number = visited_edges[current_edge] - 1
        visited_edges.update({current_edge: updated_count_number})
        raise Exception("Unknown Jump-Type")


def sym_exec_ins(params, block, statement, func_call, current_func_name):
    global MSIZE
    global visited_pcs
    global solver
    global vertices
    global edges
    global blocks
    global calls_affect_state
    global instructions
    global env_dict

    stack = params.stack
    mem = params.mem
    memory = params.memory
    global_state = params.global_state
    sha3_list = params.sha3_list
    path_conditions_and_vars = params.path_conditions_and_vars
    analysis = params.analysis
    calls = params.calls
    overflow_pcs = params.overflow_pcs
    defs, uses = emit_stmt(path, statement)
    print(defs)
    print(uses)
    # hex value tranformed to int type (base 10)
    # var remain to strings

    # no need to care about const
    # its gonna be

    # push the def vars to the stack
    # for i in range(len(uses) - 1, -1, -1):
    #     stack.insert(0, uses[i])

    instr = statement[1]
    visited_pcs.add(global_state["pc"])

    instr_parts = str.split(instr, " ")
    opcode = instr_parts[0]

    if uses == ["CALLER"]:
        env_dict[defs[0]] = global_state["sender_address"]

    if opcode == "INVALID":
        return
    elif opcode == "ASSERTFAIL":
        return

    # collecting the analysis result by calling this skeletal function
    # this should be done before symbolically executing the instruction,
    # since SE will modify the stack and mem

    log.debug("==============================")
    log.debug("EXECUTING: " + instr)
    print("==============================")
    print("EXECUTING: " + instr)

    # print(block.ident)
    # print(instr)
    if opcode == "STOP":
        global_state["pc"] = global_state["pc"] + 1
        return
    elif opcode == "ADD":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            # Type conversion is needed when they are mismatched
            if isReal(first) and isSymbolic(second):
                first = BitVecVal(first, 256)
                computed = first + second
            elif isSymbolic(first) and isReal(second):
                second = BitVecVal(second, 256)
                computed = first + second
            else:
                # both are real and we need to manually modulus with 2 ** 256
                # if both are symbolic z3 takes care of modulus automatically
                computed = (first + second) % (2**256)
            computed = simplify(computed) if is_expr(computed) else computed

            if not isAllReal(computed, first):
                solver.push()
                solver.add(UGT(first, computed))
                if check_sat(solver) == sat:
                    global_problematic_pcs['integer_overflow'].append(
                        Overflow(global_state['pc'] - 1, solver.model())
                    )
                    overflow_pcs.append(global_state['pc'] - 1)
                solver.pop()

            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif opcode == "MUL":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isReal(first) and isSymbolic(second):
                first = BitVecVal(first, 256)
            elif isSymbolic(first) and isReal(second):
                second = BitVecVal(second, 256)
            computed = first * second & UNSIGNED_BOUND_NUMBER
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif opcode == "SUB":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isReal(first) and isSymbolic(second):
                first = BitVecVal(first, 256)
                computed = first - second
            elif isSymbolic(first) and isReal(second):
                second = BitVecVal(second, 256)
                computed = first - second
            else:
                computed = (first - second) % (2**256)
            computed = simplify(computed) if is_expr(computed) else computed

            if not isAllReal(first, second):
                solver.push()
                solver.add(UGT(second, first))
                if check_sat(solver) == sat:
                    global_problematic_pcs['integer_underflow'].append(
                        Underflow(global_state['pc'] - 1, solver.model())
                    )
                solver.pop()

            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif opcode == "DIV":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isAllReal(first, second):
                if second == 0:
                    computed = 0
                else:
                    first = to_unsigned(first)
                    second = to_unsigned(second)
                    computed = first / second
            else:
                first = to_symbolic(first)
                second = to_symbolic(second)
                solver.push()
                solver.add(Not(second == 0))
                if check_sat(solver) == unsat:
                    computed = 0
                else:
                    computed = UDiv(first, second)
                solver.pop()
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif opcode == "SDIV":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isAllReal(first, second):
                first = to_signed(first)
                second = to_signed(second)
                if second == 0:
                    computed = 0
                elif first == -(2**255) and second == -1:
                    computed = -(2**255)
                else:
                    sign = -1 if (first / second) < 0 else 1
                    computed = sign * (abs(first) / abs(second))
            else:
                first = to_symbolic(first)
                second = to_symbolic(second)
                solver.push()
                solver.add(Not(second == 0))
                if check_sat(solver) == unsat:
                    computed = 0
                else:
                    solver.push()
                    solver.add(Not(And(first == -(2**255), second == -1)))
                    if check_sat(solver) == unsat:
                        computed = -(2**255)
                    else:
                        solver.push()
                        solver.add(first / second < 0)
                        sign = -1 if check_sat(solver) == sat else 1
                        z3_abs = lambda x: If(x >= 0, x, -x)
                        first = z3_abs(first)
                        second = z3_abs(second)
                        computed = sign * (first / second)
                        solver.pop()
                    solver.pop()
                solver.pop()
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif opcode == "MOD":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isAllReal(first, second):
                if second == 0:
                    computed = 0
                else:
                    first = to_unsigned(first)
                    second = to_unsigned(second)
                    computed = first % second & UNSIGNED_BOUND_NUMBER

            else:
                first = to_symbolic(first)
                second = to_symbolic(second)

                solver.push()
                solver.add(Not(second == 0))
                if check_sat(solver) == unsat:
                    # it is provable that second is indeed equal to zero
                    computed = 0
                else:
                    computed = URem(first, second)
                solver.pop()

            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif opcode == "SMOD":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isAllReal(first, second):
                if second == 0:
                    computed = 0
                else:
                    first = to_signed(first)
                    second = to_signed(second)
                    sign = -1 if first < 0 else 1
                    computed = sign * (abs(first) % abs(second))
            else:
                first = to_symbolic(first)
                second = to_symbolic(second)

                solver.push()
                solver.add(Not(second == 0))
                if check_sat(solver) == unsat:
                    # it is provable that second is indeed equal to zero
                    computed = 0
                else:
                    solver.push()
                    solver.add(first < 0)  # check sign of first element
                    sign = (
                        BitVecVal(-1, 256)
                        if check_sat(solver) == sat
                        else BitVecVal(1, 256)
                    )
                    solver.pop()

                    z3_abs = lambda x: If(x >= 0, x, -x)
                    first = z3_abs(first)
                    second = z3_abs(second)

                    computed = sign * (first % second)
                solver.pop()

            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif opcode == "ADDMOD":
        if len(stack) > 2:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            third = stack.pop(0)

            if isAllReal(first, second, third):
                if third == 0:
                    computed = 0
                else:
                    computed = (first + second) % third
            else:
                first = to_symbolic(first)
                second = to_symbolic(second)
                solver.push()
                solver.add(Not(third == 0))
                if check_sat(solver) == unsat:
                    computed = 0
                else:
                    first = ZeroExt(256, first)
                    second = ZeroExt(256, second)
                    third = ZeroExt(256, third)
                    computed = (first + second) % third
                    computed = Extract(255, 0, computed)
                solver.pop()
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif opcode == "MULMOD":
        if len(stack) > 2:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            third = stack.pop(0)

            if isAllReal(first, second, third):
                if third == 0:
                    computed = 0
                else:
                    computed = (first * second) % third
            else:
                first = to_symbolic(first)
                second = to_symbolic(second)
                solver.push()
                solver.add(Not(third == 0))
                if check_sat(solver) == unsat:
                    computed = 0
                else:
                    first = ZeroExt(256, first)
                    second = ZeroExt(256, second)
                    third = ZeroExt(256, third)
                    computed = URem(first * second, third)
                    computed = Extract(255, 0, computed)
                solver.pop()
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif opcode == "EXP":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            base = stack.pop(0)
            exponent = stack.pop(0)
            # Type conversion is needed when they are mismatched
            if isAllReal(base, exponent):
                computed = pow(base, exponent, 2**256)
            else:
                # The computed value is unknown, this is because power is
                # not supported in bit-vector theory
                new_var_name = gen.gen_arbitrary_var()
                computed = BitVec(new_var_name, 256)
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif opcode == "SIGNEXTEND":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isAllReal(first, second):
                if first >= 32 or first < 0:
                    computed = second
                else:
                    signbit_index_from_right = 8 * first + 7
                    if second & (1 << signbit_index_from_right):
                        computed = second | (2**256 - (1 << signbit_index_from_right))
                    else:
                        computed = second & ((1 << signbit_index_from_right) - 1)
            else:
                first = to_symbolic(first)
                second = to_symbolic(second)
                solver.push()
                solver.add(Not(Or(first >= 32, first < 0)))
                if check_sat(solver) == unsat:
                    computed = second
                else:
                    signbit_index_from_right = 8 * first + 7
                    solver.push()
                    solver.add(second & (1 << signbit_index_from_right) == 0)
                    if check_sat(solver) == unsat:
                        computed = second | (2**256 - (1 << signbit_index_from_right))
                    else:
                        computed = second & ((1 << signbit_index_from_right) - 1)
                    solver.pop()
                solver.pop()
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    #
    #  10s: Comparison and Bitwise Logic Operations
    #
    elif opcode == "LT":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)

            if isAllReal(first, second):
                first = to_unsigned(first)
                second = to_unsigned(second)
                if first < second:
                    computed = 1
                else:
                    computed = 0
            else:
                computed = If(ULT(first, second), BitVecVal(1, 256), BitVecVal(0, 256))
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "GT":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)

            if isAllReal(first, second):
                first = to_unsigned(first)
                second = to_unsigned(second)
                if first > second:
                    computed = 1
                else:
                    computed = 0
            else:
                computed = If(UGT(first, second), BitVecVal(1, 256), BitVecVal(0, 256))
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "SLT":  # Not fully faithful to signed comparison
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isAllReal(first, second):
                first = to_signed(first)
                second = to_signed(second)
                if first < second:
                    computed = 1
                else:
                    computed = 0
            else:
                computed = If(first < second, BitVecVal(1, 256), BitVecVal(0, 256))
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "SGT":  # Not fully faithful to signed comparison
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isAllReal(first, second):
                first = to_signed(first)
                second = to_signed(second)
                if first > second:
                    computed = 1
                else:
                    computed = 0
            else:
                computed = If(first > second, BitVecVal(1, 256), BitVecVal(0, 256))
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "EQ":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isAllReal(first, second):
                if first == second:
                    computed = 1
                else:
                    computed = 0
            else:
                computed = If(first == second, BitVecVal(1, 256), BitVecVal(0, 256))
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "ISZERO":
        # Tricky: this instruction works on both boolean and integer,
        # when we have a symbolic expression, type error might occur
        # Currently handled by try and catch
        if len(opcode) > 0:
            global_state["pc"] = global_state["pc"] + 1
            # first = stack.pop(0)
            first = uses[0]
            if isReal(first):
                if first == 0:
                    computed = 1
                else:
                    computed = 0
            else:
                if first in var_to_source.keys():
                    first = var_to_source[first]
                    computed = If(first == 0, BitVecVal(1, 256), BitVecVal(0, 256))
            # computed = simplify(computed) if is_expr(computed) else computed
            # stack.insert(0, computed)
            var_to_source[defs[0]] = computed
        else:
            raise ValueError("STACK underflow")
    elif opcode == "AND":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            computed = first & second
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "OR":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)

            computed = first | second
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)

        else:
            raise ValueError("STACK underflow")
    elif opcode == "XOR":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)

            computed = first ^ second
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)

        else:
            raise ValueError("STACK underflow")
    elif opcode == "NOT":
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            computed = (~first) & UNSIGNED_BOUND_NUMBER
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "BYTE":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            byte_index = 32 - first - 1
            second = stack.pop(0)

            if isAllReal(first, second):
                if first >= 32 or first < 0:
                    computed = 0
                else:
                    computed = second & (255 << (8 * byte_index))
                    computed = computed >> (8 * byte_index)
            else:
                first = to_symbolic(first)
                second = to_symbolic(second)
                solver.push()
                solver.add(Not(Or(first >= 32, first < 0)))
                if check_sat(solver) == unsat:
                    computed = 0
                else:
                    computed = second & (255 << (8 * byte_index))
                    computed = computed >> (8 * byte_index)
                solver.pop()
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError("STACK underflow")
    #
    # 20s: SHA3/KECCAK256
    #
    elif opcode in ["KECCAK256", "SHA3"]:
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            s0 = stack.pop(0)  # 0
            s1 = stack.pop(0)  # 64
            slot = None
            if isAllReal(s0, s1):
                # simulate the hashing of sha3
                data = [str(x) for x in memory[s0 : s0 + s1]]

                # *Slot id in memory[63] <= MSTORE(64, slot)
                slot = memory[63]
                position = "".join(data)
                position = re.sub("[\s+]", "", position)
                position = zlib.compress(six.b(position), 9)
                position = base64.b64encode(position)
                position = position.decode("utf-8", "strict")
                if position in sha3_list:
                    stack.insert(0, sha3_list[position])
                else:
                    new_var_name = gen.gen_arbitrary_var()
                    new_var = BitVec(new_var_name, 256)
                    sha3_list[position] = new_var
                    stack.insert(0, new_var)
            else:
                # push into the execution a fresh symbolic variable
                new_var_name = gen.gen_arbitrary_var()
                new_var = BitVec(new_var_name, 256)
                path_conditions_and_vars[new_var_name] = new_var
                stack.insert(0, new_var)

        else:
            raise ValueError("STACK underflow")
    #
    # 30s: Environment Information
    #
    elif opcode == "ADDRESS":  # get address of currently executing account
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, path_conditions_and_vars["Ia"])
    elif opcode == "BALANCE":
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            address = stack.pop(0)

            new_var_name = gen.gen_balance_var()
            if new_var_name in path_conditions_and_vars:
                new_var = path_conditions_and_vars[new_var_name]
            else:
                new_var = BitVec(new_var_name, 256)
                path_conditions_and_vars[new_var_name] = new_var
            if isReal(address):
                hashed_address = "concrete_address_" + str(address)
            else:
                hashed_address = str(address)
            global_state["balance"][hashed_address] = new_var
            stack.insert(0, new_var)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "CALLER":  # get caller address
        # that is directly responsible for this execution
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["sender_address"])
    elif opcode == "ORIGIN":  # get execution origination address
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["origin"])
    elif opcode == "CALLVALUE":  # get value of this transaction
        global_state["pc"] = global_state["pc"] + 1
        # stack.insert(0, global_state["value"])
        var_to_source[defs[0]] = global_state["value"]
        # buy function feature: msg.value to transfer the token

    elif opcode == "CALLDATALOAD":  # from inputter data from environment
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            position = stack.pop(0)
            new_var_name = gen.gen_data_var(position)
            if new_var_name in path_conditions_and_vars:
                new_var = path_conditions_and_vars[new_var_name]
            else:
                new_var = BitVec(new_var_name, 256)
                path_conditions_and_vars[new_var_name] = new_var
            stack.insert(0, new_var)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "CALLDATASIZE":
        global_state["pc"] = global_state["pc"] + 1
        new_var_name = gen.gen_data_size()
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    elif opcode == "CALLDATACOPY":  # Copy inputter data to memory
        #  TODO: Don't know how to simulate this yet
        if len(stack) > 2:
            global_state["pc"] = global_state["pc"] + 1
            stack.pop(0)
            stack.pop(0)
            stack.pop(0)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "CODESIZE":
        global_state["pc"] = global_state["pc"] + 1
        if g_disasm_file.endswith(".disasm"):
            evm_file_name = g_disasm_file[:-7]
        else:
            evm_file_name = g_disasm_file
        with open(evm_file_name, "r") as evm_file:
            evm = evm_file.read()[:-1]
            code_size = len(evm) / 2
            stack.insert(0, code_size)
    elif opcode == "CODECOPY":
        if len(stack) > 2:
            global_state["pc"] = global_state["pc"] + 1
            mem_location = stack.pop(0)
            code_from = stack.pop(0)
            no_bytes = stack.pop(0)
            current_miu_i = global_state["miu_i"]

            if isAllReal(mem_location, current_miu_i, code_from, no_bytes):
                temp = int(math.ceil((mem_location + no_bytes) / float(32)))
                if temp > current_miu_i:
                    current_miu_i = temp

                if g_disasm_file.endswith(".disasm"):
                    evm_file_name = g_disasm_file[:-7]
                else:
                    evm_file_name = g_disasm_file
                with open(evm_file_name, "r") as evm_file:
                    evm = evm_file.read()[:-1]
                    start = code_from * 2
                    end = start + no_bytes * 2
                    code = evm[start:end]
                mem[mem_location] = int(code, 16)
            else:
                new_var_name = gen.gen_code_var("Ia", code_from, no_bytes)
                if new_var_name in path_conditions_and_vars:
                    new_var = path_conditions_and_vars[new_var_name]
                else:
                    new_var = BitVec(new_var_name, 256)
                    path_conditions_and_vars[new_var_name] = new_var

                temp = ((mem_location + no_bytes) / 32) + 1
                current_miu_i = to_symbolic(current_miu_i)
                expression = current_miu_i < temp
                solver.push()
                solver.add(expression)
                if MSIZE:
                    if check_sat(solver) != unsat:
                        current_miu_i = If(expression, temp, current_miu_i)
                solver.pop()
                mem.clear()  # very conservative
                mem[str(mem_location)] = new_var
            global_state["miu_i"] = current_miu_i
        else:
            raise ValueError("STACK underflow")
    elif opcode == "RETURNDATACOPY":
        if len(stack) > 2:
            global_state["pc"] += 1
            stack.pop(0)
            stack.pop(0)
            stack.pop(0)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "RETURNDATASIZE":
        global_state["pc"] += 1
        new_var_name = gen.gen_arbitrary_var()
        new_var = BitVec(new_var_name, 256)
        stack.insert(0, new_var)
    elif opcode == "GASPRICE":
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["gas_price"])
    elif opcode == "EXTCODESIZE":
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            address = stack.pop(0)

            # not handled yet
            new_var_name = gen.gen_code_size_var(address)
            if new_var_name in path_conditions_and_vars:
                new_var = path_conditions_and_vars[new_var_name]
            else:
                new_var = BitVec(new_var_name, 256)
                path_conditions_and_vars[new_var_name] = new_var
            stack.insert(0, new_var)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "EXTCODECOPY":
        if len(stack) > 3:
            global_state["pc"] = global_state["pc"] + 1
            address = stack.pop(0)
            mem_location = stack.pop(0)
            code_from = stack.pop(0)
            no_bytes = stack.pop(0)
            current_miu_i = global_state["miu_i"]

            new_var_name = gen.gen_code_var(address, code_from, no_bytes)
            if new_var_name in path_conditions_and_vars:
                new_var = path_conditions_and_vars[new_var_name]
            else:
                new_var = BitVec(new_var_name, 256)
                path_conditions_and_vars[new_var_name] = new_var

            temp = ((mem_location + no_bytes) / 32) + 1
            current_miu_i = to_symbolic(current_miu_i)
            expression = current_miu_i < temp
            solver.push()
            solver.add(expression)
            if MSIZE:
                if check_sat(solver) != unsat:
                    current_miu_i = If(expression, temp, current_miu_i)
            solver.pop()
            mem.clear()  # very conservative
            mem[str(mem_location)] = new_var
            global_state["miu_i"] = current_miu_i
        else:
            raise ValueError("STACK underflow")
    #
    #  40s: Block Information
    #
    elif opcode == "BLOCKHASH":  # information from block header
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            stack.pop(0)
            new_var_name = "IH_blockhash"
            if new_var_name in path_conditions_and_vars:
                new_var = path_conditions_and_vars[new_var_name]
            else:
                new_var = BitVec(new_var_name, 256)
                path_conditions_and_vars[new_var_name] = new_var
            stack.insert(0, new_var)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "COINBASE":  # information from block header
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["currentCoinbase"])
    elif opcode == "TIMESTAMP":  # information from block header
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["currentTimestamp"])
    elif opcode == "NUMBER":  # information from block header
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["currentNumber"])
    elif opcode == "DIFFICULTY":  # information from block header
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["currentDifficulty"])
    elif opcode == "GASLIMIT":  # information from block header
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["currentGasLimit"])
    #
    #  50s: Stack, Memory, Storage, and Flow Information
    #
    elif opcode == "POP":
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            stack.pop(0)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "MLOAD":
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            address = stack.pop(0)
            current_miu_i = global_state["miu_i"]
            if isAllReal(address, current_miu_i) and address in mem:
                temp = int(math.ceil((address + 32) / float(32)))
                if temp > current_miu_i:
                    current_miu_i = temp
                value = mem[address]
                stack.insert(0, value)
            else:
                temp = ((address + 31) / 32) + 1
                current_miu_i = to_symbolic(current_miu_i)
                expression = current_miu_i < temp
                solver.push()
                solver.add(expression)
                if MSIZE:
                    if check_sat(solver) != unsat:
                        # this means that it is possibly that current_miu_i < temp
                        current_miu_i = If(expression, temp, current_miu_i)
                solver.pop()
                new_var_name = gen.gen_mem_var(address)
                if new_var_name in path_conditions_and_vars:
                    new_var = path_conditions_and_vars[new_var_name]
                else:
                    new_var = BitVec(new_var_name, 256)
                    path_conditions_and_vars[new_var_name] = new_var
                stack.insert(0, new_var)
                if isReal(address):
                    mem[address] = new_var
                else:
                    mem[str(address)] = new_var
            global_state["miu_i"] = current_miu_i
        else:
            raise ValueError("STACK underflow")
    elif opcode == "MSTORE":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            stored_address = stack.pop(0)
            stored_value = stack.pop(0)
            # MSTORE slotid to MEM32

            current_miu_i = global_state["miu_i"]
            if isReal(stored_address):
                # preparing data for hashing later
                old_size = len(memory) // 32
                new_size = ceil32(stored_address + 32) // 32
                mem_extend = (new_size - old_size) * 32
                memory.extend([0] * mem_extend)
                value = stored_value

                for i in range(31, -1, -1):
                    memory[stored_address + i] = value % 256
                    value /= 256
            if isAllReal(stored_address, current_miu_i):
                temp = int(math.ceil((stored_address + 32) / float(32)))
                if temp > current_miu_i:
                    current_miu_i = temp
                # note that the stored_value could be symbolic
                mem[stored_address] = stored_value
            else:
                temp = ((stored_address + 31) / 32) + 1
                expression = current_miu_i < temp
                solver.push()
                solver.add(expression)
                if MSIZE:
                    if check_sat(solver) != unsat:
                        # this means that it is possibly that current_miu_i < temp
                        current_miu_i = If(expression, temp, current_miu_i)
                solver.pop()
                mem.clear()  # very conservative
                mem[str(stored_address)] = stored_value
            global_state["miu_i"] = current_miu_i
        else:
            raise ValueError("STACK underflow")
    elif opcode == "MSTORE8":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            stored_address = stack.pop(0)
            temp_value = stack.pop(0)
            stored_value = temp_value % 256  # get the least byte
            current_miu_i = global_state["miu_i"]
            if isAllReal(stored_address, current_miu_i):
                temp = int(math.ceil((stored_address + 1) / float(32)))
                if temp > current_miu_i:
                    current_miu_i = temp
                # note that the stored_value could be symbolic
                mem[stored_address] = stored_value
            else:
                temp = (stored_address / 32) + 1
                if isReal(current_miu_i):
                    current_miu_i = BitVecVal(current_miu_i, 256)
                expression = current_miu_i < temp
                solver.push()
                solver.add(expression)
                if MSIZE:
                    if check_sat(solver) != unsat:
                        # this means that it is possibly that current_miu_i < temp
                        current_miu_i = If(expression, temp, current_miu_i)
                solver.pop()
                mem.clear()  # very conservative
                mem[str(stored_address)] = stored_value
            global_state["miu_i"] = current_miu_i
        else:
            raise ValueError("STACK underflow")
    elif opcode == "SLOAD":
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            position = stack.pop(0)

            if isReal(position) and position in global_state["Ia"]:
                value = global_state["Ia"][position]
                stack.insert(0, value)
            else:
                if str(position) in global_state["Ia"]:
                    value = global_state["Ia"][str(position)]
                    stack.insert(0, value)
                else:
                    if is_expr(position):
                        position = simplify(position)
                    new_var_name = gen.gen_owner_store_var(position)

                    if new_var_name in path_conditions_and_vars:
                        new_var = path_conditions_and_vars[new_var_name]
                    else:
                        new_var = BitVec(new_var_name, 256)
                        path_conditions_and_vars[new_var_name] = new_var
                    stack.insert(0, new_var)
                    if isReal(position):
                        global_state["Ia"][position] = new_var
                    else:
                        global_state["Ia"][str(position)] = new_var
        else:
            raise ValueError("STACK underflow")

    elif opcode == "SSTORE":
        if len(stack) > 1:
            for call_pc in calls:
                calls_affect_state[call_pc] = True
            global_state["pc"] = global_state["pc"] + 1
            stored_address = stack.pop(0)
            stored_value = stack.pop(0)

            if isReal(stored_address):
                # note that the stored_value could be unknown
                global_state["Ia"][stored_address] = stored_value
            else:
                # note that the stored_value could be unknown
                global_state["Ia"][str(stored_address)] = stored_value
        else:
            raise ValueError("STACK underflow")
    elif opcode == "JUMP":
        if len(stack) > 0:
            target_block = stack.pop(0)
            # next_block = blocks[hex(target_block)]
            # block.successors.append(next_block)
            # target_address = stack.pop(0)
            # if isSymbolic(target_address):
            #     try:
            #         target_address = int(str(simplify(target_address)))
            #     except:
            #         raise TypeError("Target address must be an integer")
            # # vertices[block].set_jump_target(target_address)
            # if target_address not in edges[block]:
            #     edges[block].append(target_address)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "JUMPI":
        # We need to prepare two branches
        if len(stack) > 1:
            target_address = stack.pop(0)
            # next_block = blocks[hex(target_block)]
            # block.successors.append(next_block)
            # if isSymbolic(target_address):
            #     try:
            #         target_address = int(str(simplify(target_address)))
            #     except:
            #         raise TypeError("Target address must be an integer")
            # vertices[block].set_jump_target(target_address)
            flag = stack.pop(0)
            branch_expression = BitVecVal(0, 1) == BitVecVal(1, 1)
            if isReal(flag):
                if flag != 0:
                    branch_expression = True
            else:
                branch_expression = flag != 0
            block.set_branch_expression(branch_expression)
            # # vertices[block].set_branch_expression(branch_expression)
            # if target_address not in edges[block]:
            #     edges[block].append(target_address)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "PC":
        stack.insert(0, global_state["pc"])
        global_state["pc"] = global_state["pc"] + 1
    elif opcode == "MSIZE":
        global_state["pc"] = global_state["pc"] + 1
        msize = 32 * global_state["miu_i"]
        stack.insert(0, msize)
    elif opcode == "GAS":
        # In general, we do not have this precisely. It depends on both
        # the initial gas and the amount has been depleted
        # we need o think about this in the future, in case precise gas
        # can be tracked
        global_state["pc"] = global_state["pc"] + 1
        new_var_name = gen.gen_gas_var()
        new_var = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    elif opcode == "JUMPDEST":
        # Literally do nothing
        global_state["pc"] = global_state["pc"] + 1
    #
    #  60s & 70s: Push Operations
    #  No push op in gigahorse IR
    elif opcode.startswith("PUSH", 0):  # this is a push instruction
        position = int(opcode[4:], 10)
        global_state["pc"] = global_state["pc"] + 1 + position
        pushed_value = int(instr_parts[1], 16)
        stack.insert(0, pushed_value)
        if global_params.UNIT_TEST == 3:  # test evm symbolic
            stack[0] = BitVecVal(stack[0], 256)

    elif opcode == "CONST":
        for i in range(len(defs) - 1, -1, -1):
            if isReal(defs[i]):
                stack.insert(0, defs[i])
    #
    #  80s: Duplication Operations
    #
    elif opcode.startswith("DUP", 0):
        global_state["pc"] = global_state["pc"] + 1
        position = int(opcode[3:], 10) - 1
        if len(stack) > position:
            duplicate = stack[position]
            stack.insert(0, duplicate)
        else:
            raise ValueError("STACK underflow")

    #
    #  90s: Swap Operations
    #
    elif opcode.startswith("SWAP", 0):
        global_state["pc"] = global_state["pc"] + 1
        position = int(opcode[4:], 10)
        if len(stack) > position:
            temp = stack[position]
            stack[position] = stack[0]
            stack[0] = temp
        else:
            raise ValueError("STACK underflow")

    #
    #  a0s: Logging Operations
    #
    elif opcode in ("LOG0", "LOG1", "LOG2", "LOG3", "LOG4"):
        global_state["pc"] = global_state["pc"] + 1
        # We do not simulate these log operations
        num_of_pops = 2 + int(opcode[3:])
        while num_of_pops > 0:
            stack.pop(0)
            num_of_pops -= 1

    #
    #  f0s: System Operations
    #
    elif opcode in ["CREATE", "CREATE2"]:
        if len(stack) > 2:
            global_state["pc"] += 1
            stack.pop(0)
            stack.pop(0)
            stack.pop(0)
            new_var_name = gen.gen_arbitrary_var()
            new_var = BitVec(new_var_name, 256)
            stack.insert(0, new_var)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "CALL":
        # TODO: Need to handle miu_i
        if len(stack) > 6:
            calls.append(global_state["pc"])
            for call_pc in calls:
                if call_pc not in calls_affect_state:
                    calls_affect_state[call_pc] = False
            global_state["pc"] = global_state["pc"] + 1
            outgas = stack.pop(0)
            recipient = stack.pop(0)
            transfer_amount = stack.pop(0)
            start_data_input = stack.pop(0)
            size_data_input = stack.pop(0)
            start_data_output = stack.pop(0)
            size_data_ouput = stack.pop(0)
            log.info(recipient)
            log.info(transfer_amount)
            print(recipient)
            print(transfer_amount)
            # in the paper, it is shaky when the size of data output is
            # min of stack[6] and the | o |

            if isReal(transfer_amount):
                if transfer_amount == 0:
                    stack.insert(0, 1)  # x = 0
                    return

            # Let us ignore the call depth
            balance_ia = global_state["balance"]["Ia"]
            is_enough_fund = transfer_amount <= balance_ia
            solver.push()
            solver.add(is_enough_fund)

            if check_sat(solver) == unsat:
                # this means not enough fund, thus the execution will result in exception
                solver.pop()
                stack.insert(0, 0)  # x = 0
            else:
                # the execution is possibly okay
                stack.insert(0, 1)  # x = 1
                solver.pop()
                solver.add(is_enough_fund)
                path_conditions_and_vars["path_condition"].append(is_enough_fund)
                last_idx = len(path_conditions_and_vars["path_condition"]) - 1
                # analysis["time_dependency_bug"][last_idx] = global_state["pc"] - 1
                new_balance_ia = balance_ia - transfer_amount
                global_state["balance"]["Ia"] = new_balance_ia
                address_is = path_conditions_and_vars["Is"]
                address_is = address_is & CONSTANT_ONES_159
                boolean_expression = recipient != address_is
                solver.push()
                solver.add(boolean_expression)
                if check_sat(solver) == unsat:
                    solver.pop()
                    new_balance_is = global_state["balance"]["Is"] + transfer_amount
                    global_state["balance"]["Is"] = new_balance_is
                else:
                    solver.pop()
                    if isReal(recipient):
                        new_address_name = "concrete_address_" + str(recipient)
                    else:
                        new_address_name = gen.gen_arbitrary_address_var()
                    old_balance_name = gen.gen_arbitrary_var()
                    old_balance = BitVec(old_balance_name, 256)
                    path_conditions_and_vars[old_balance_name] = old_balance
                    constraint = old_balance >= 0
                    solver.add(constraint)
                    path_conditions_and_vars["path_condition"].append(constraint)
                    new_balance = old_balance + transfer_amount
                    global_state["balance"][new_address_name] = new_balance
        else:
            raise ValueError("STACK underflow")
    elif opcode == "CALLCODE":
        # TODO: Need to handle miu_i
        if len(stack) > 6:
            calls.append(global_state["pc"])
            for call_pc in calls:
                if call_pc not in calls_affect_state:
                    calls_affect_state[call_pc] = False
            global_state["pc"] = global_state["pc"] + 1
            outgas = stack.pop(0)
            recipient = stack.pop(0)  # this is not used as recipient

            transfer_amount = stack.pop(0)
            start_data_input = stack.pop(0)
            size_data_input = stack.pop(0)
            start_data_output = stack.pop(0)
            size_data_ouput = stack.pop(0)
            # in the paper, it is shaky when the size of data output is
            # min of stack[6] and the | o |

            if isReal(transfer_amount):
                if transfer_amount == 0:
                    stack.insert(0, 1)  # x = 0
                    return

            # Let us ignore the call depth
            balance_ia = global_state["balance"]["Ia"]
            is_enough_fund = transfer_amount <= balance_ia
            solver.push()
            solver.add(is_enough_fund)

            if check_sat(solver) == unsat:
                # this means not enough fund, thus the execution will result in exception
                solver.pop()
                stack.insert(0, 0)  # x = 0
            else:
                # the execution is possibly okay
                stack.insert(0, 1)  # x = 1
                solver.pop()
                solver.add(is_enough_fund)
                path_conditions_and_vars["path_condition"].append(is_enough_fund)
                last_idx = len(path_conditions_and_vars["path_condition"]) - 1
        else:
            raise ValueError("STACK underflow")
    elif opcode in ("DELEGATECALL", "STATICCALL"):
        if len(stack) > 5:
            global_state["pc"] += 1
            stack.pop(0)
            recipient = stack.pop(0)

            stack.pop(0)
            stack.pop(0)
            stack.pop(0)
            stack.pop(0)
            new_var_name = gen.gen_arbitrary_var()
            new_var = BitVec(new_var_name, 256)
            stack.insert(0, new_var)
        else:
            raise ValueError("STACK underflow")
    elif opcode == "REVERT":
        if len(stack) > 1:
            stack.pop(0)
            pass
    elif opcode == "RETURN":
        # TODO: Need to handle miu_i
        if len(stack) > 1:
            if opcode == "REVERT":
                revertible_overflow_pcs.update(overflow_pcs)
                global_state["pc"] = global_state["pc"] + 1
            stack.pop(0)
            stack.pop(0)
            # TODO
            pass
        else:
            raise ValueError("STACK underflow")
    elif opcode in ("SELFDESTRUCT", "SUICIDE"):
        global_state["pc"] = global_state["pc"] + 1
        recipient = stack.pop(0)
        transfer_amount = global_state["balance"]["Ia"]
        global_state["balance"]["Ia"] = 0
        if isReal(recipient):
            new_address_name = "concrete_address_" + str(recipient)
        else:
            new_address_name = gen.gen_arbitrary_address_var()
        old_balance_name = gen.gen_arbitrary_var()
        old_balance = BitVec(old_balance_name, 256)
        path_conditions_and_vars[old_balance_name] = old_balance
        constraint = old_balance >= 0
        solver.add(constraint)
        path_conditions_and_vars["path_condition"].append(constraint)
        new_balance = old_balance + transfer_amount
        global_state["balance"][new_address_name] = new_balance
        # TODO
        return

    # brand new opcodes
    elif opcode == "SHL":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            # *For selector to shift left 224 bits
            # EXP
            base = 2
            exponent = stack.pop(0)
            # Type conversion is needed when they are mismatched
            if isAllReal(base, exponent):
                computed = pow(base, exponent, 2**256)
            else:
                # The computed value is unknown, this is because power is
                # not supported in bit-vector theory
                new_var_name = gen.gen_arbitrary_var()
                computed = BitVec(new_var_name, 256)
            computed = simplify(computed) if is_expr(computed) else computed

            # MUL
            first = computed
            second = stack.pop(0)
            if isReal(first) and isSymbolic(second):
                first = BitVecVal(first, 256)
            elif isSymbolic(first) and isReal(second):
                second = BitVecVal(second, 256)
            computed = first * second & UNSIGNED_BOUND_NUMBER
            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)

            # *Simpler model
            # first = stack.pop(0)
            # second = stack.pop(0)
            # # Type conversion is needed when they are mismatched
            # if isReal(first) and isSymbolic(second):
            #     first = BitVecVal(first, 256)
            #     computed = first + second
            # elif isSymbolic(first) and isReal(second):
            #     second = BitVecVal(second, 256)
            #     computed = first + second
            # else:
            #     # both are real and we need to manually modulus with 2 ** 256
            #     # if both are symbolic z3 takes care of modulus automatically
            #     computed = mod((second + 2 ^ first), 2 ^ 256)

            # computed = simplify(computed) if is_expr(computed) else computed
            # stack.insert(0, computed)
        else:
            raise ValueError("STACK underflow")

    elif opcode == "SHR":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            # # EXP
            # base = 2
            # exponent = stack.pop(0)
            # # Type conversion is needed when they are mismatched
            # if isAllReal(base, exponent):
            #     computed = pow(base, exponent, 2**256)
            # else:
            #     # The computed value is unknown, this is because power is
            #     # not supported in bit-vector theory
            #     new_var_name = gen.gen_arbitrary_var()
            #     computed = BitVec(new_var_name, 256)
            # computed = simplify(computed) if is_expr(computed) else computed

            # # DIV
            # first = computed
            # second = stack.pop(0)
            # if isAllReal(first, second):
            #     if second == 0:
            #         computed = 0
            #     else:
            #         first = to_unsigned(first)
            #         second = to_unsigned(second)
            #         computed = first / second
            # else:
            #     first = to_symbolic(first)
            #     second = to_symbolic(second)
            #     solver.push()
            #     solver.add(Not(second == 0))
            #     if check_sat(solver) == unsat:
            #         computed = 0
            #     else:
            #         computed = UDiv(first, second)
            #     solver.pop()
            # computed = simplify(computed) if is_expr(computed) else computed
            # stack.insert(0, computed)

            # *Simpler model
            first = stack.pop(0)
            second = stack.pop(0)
            # Type conversion is needed when they are mismatched
            if isReal(first) and isSymbolic(second):
                first = BitVecVal(first, 256)
                computed = first + second
            elif isSymbolic(first) and isReal(second):
                second = BitVecVal(second, 256)
                computed = first + second
            else:
                # both are real and we need to manually modulus with 2 ** 256
                # if both are symbolic z3 takes care of modulus automatically
                computed = mod((second + 2 ^ first), 2 ^ 256)

            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError("STACK underflow")

    elif opcode == "SAR":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            # # EXP
            # base = 2
            # exponent = stack.pop(0)
            # # Type conversion is needed when they are mismatched
            # if isAllReal(base, exponent):
            #     computed = pow(base, exponent, 2**256)
            # else:
            #     # The computed value is unknown, this is because power is
            #     # not supported in bit-vector theory
            #     new_var_name = gen.gen_arbitrary_var()
            #     computed = BitVec(new_var_name, 256)
            # computed = simplify(computed) if is_expr(computed) else computed

            # # not equivalent to SDIV
            # first = computed
            # second = stack.pop(0)
            # if isAllReal(first, second):
            #     first = to_unsigned(first)
            #     second = to_signed(second)
            #     if second == 0:
            #         computed = 0
            #     elif first == -2**255 and second == -1:
            #         computed = -2**255
            #     else:
            #         sign = -1 if (first / second) < 0 else 1
            #         computed = sign * (abs(first) / abs(second))
            # else:
            #     first = to_symbolic(first)
            #     second = to_symbolic(second)
            #     solver.push()
            #     solver.add(Not(second == 0))
            #     if check_sat(solver) == unsat:
            #         computed = 0
            #     else:
            #         solver.push()
            #         solver.add(Not(And(first == -2**255, second == -1)))
            #         if check_sat(solver) == unsat:
            #             computed = -2**255
            #         else:
            #             solver.push()
            #             solver.add(first / second < 0)
            #             sign = -1 if check_sat(solver) == sat else 1
            #             def z3_abs(x): return If(x >= 0, x, -x)
            #             first = z3_abs(first)
            #             second = z3_abs(second)
            #             computed = sign * (first / second)
            #             solver.pop()
            #         solver.pop()
            #     solver.pop()
            # computed = simplify(computed) if is_expr(computed) else computed
            # stack.insert(0, computed)

            # *Simpler model
            first = stack.pop(0)
            second = stack.pop(0)
            # Type conversion is needed when they are mismatched
            if isReal(first) and isSymbolic(second):
                first = BitVecVal(first, 256)
                computed = first + second
            elif isSymbolic(first) and isReal(second):
                second = BitVecVal(second, 256)
                computed = first + second
            else:
                # both are real and we need to manually modulus with 2 ** 256
                # if both are symbolic z3 takes care of modulus automatically
                computed = mod((second + 2 ^ first), 2 ^ 256)

            computed = simplify(computed) if is_expr(computed) else computed
            stack.insert(0, computed)
        else:
            raise ValueError("STACK underflow")

    elif opcode == "SELFBALANCE":
        # address(this).balance
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["currentSelfBalance"])

    elif opcode == "CHAINID":
        # chain_id = {  1 // mainnet
        #    {  2 // Morden testnet (disused)
        #    {  2 // Expanse mainnet
        #    {  3 // Ropsten testnet
        #    {  4 // Rinkeby testnet
        #    {  5 // Goerli testnet
        #    { 42 // Kovan testnet
        #    { ...
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["currentChainId"])

    elif opcode == "BASEFEE":
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["currentBaseFee"])

    elif opcode == "CALLPRIVATE":
        pass
        # for i in range(len(uses) - 1, -1, -1):
        #     stack.insert(0, uses[i])
        #     print(uses[i])
        # target_private_func = stack.pop(0)
        # next_block = blocks[hex(target_private_func)]
        # block.successors.append(next_block)
        # function argument mapping
        # statement uses mapping to private call args
        # func_id = tac_block_function[next_block]

    elif opcode == "RETURNPRIVATE":
        # for i in range(len(uses) - 1, -1, -1):
        #     stack.insert(0, uses[i])
        # return_func = stack.pop(0)
        # next_block = blocks[hex(return_func)]
        # block.successors.append(next_block)
        pass

    else:
        log.info("UNKNOWN INSTRUCTION: " + opcode)
        if global_params.UNIT_TEST == 2 or global_params.UNIT_TEST == 3:
            log.critical("Unknown instruction: %s" % opcode)
            # exit(UNKNOWN_INSTRUCTION)
        raise Exception("UNKNOWN INSTRUCTION: " + opcode)
    print(var_to_source)


if __name__ == "__main__":
    global g_disasm_file
    g_disasm_file = "./gigahorse-toolchain/.temp/eth_bnbpirates/contract.disam"
    global path
    path = "./gigahorse-toolchain/.temp/eth_bnbpirates/out/"
    run_build_cfg_and_analyze()
