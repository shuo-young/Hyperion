from multiprocessing import Process
from ir_basic_blocks import *
from z3 import *
from semantic_parser.semantic import TargetedParameters
from symbolic_execution.semantic_analysis import *
from symbolic_execution.vargenerator import *
from symbolic_execution.execution_states import (
    UNKNOWN_INSTRUCTION,
    EXCEPTION,
    PICKLE_PATH,
)
import traceback
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

global result
result = {
    "transfer": {},
    "tax": {},
    "mint": {},
    "lock": {},
    "clear": {},
    "pause": {},
    "metadata": {},
}


class Parameter:
    def __init__(self, **kwargs):
        attr_defaults = {
            "stack": [],
            "calls": [],
            "memory": [],
            "visited": [],
            "overflow_pcs": [],
            "mem": {},
            "var_to_source": {},
            "analysis": {},
            "sha3_list": {},
            "global_state": {},
            "path_conditions_and_vars": {},
            "target_params": None,
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


def generate_dot_file(target_func):
    """
    Generates a .dot file for the control flow graph based on visited_edges.

    :param visited_edges: A dictionary where keys are namedtuples representing edges and
                          values are the number of times the edge has been visited.
    :param filename: The name of the output .dot file.
    """
    filename = str(target_func) + ".dot"
    with open(filename, 'w') as f:
        f.write("digraph CFG {\n")
        f.write("    node [shape=box];\n")

        for edge, count in visited_edges.items():
            current_edge_type = visited_edges_type.get(edge, "normal")

            if current_edge_type == "private_call_return":
                color = "red"
            elif current_edge_type == "private_call_from":
                color = "blue"
            else:
                color = "black"
            f.write(
                f'    "{edge.v1.ident}" -> "{edge.v2.ident}" [label="Visited: {count}", color="{color}"];\n'
            )

        f.write("}\n")


class CustomSolver:
    def __init__(self, parallel=0, timeout=0):
        self.push_count = 0
        if parallel == 1:
            t2 = Then('simplify', 'solve-eqs', 'smt')
            _t = Then('tseitin-cnf-core', 'split-clause')
            t1 = ParThen(_t, t2)
            self.solver = OrElse(t1, t2).solver()
        else:
            self.solver = Solver()
        self.solver.set("timeout", timeout)
        self.solver.add()

    def push(self):
        self.solver.push()
        self.push_count += 1

    def pop(self):
        if self.push_count > 0:
            self.solver.pop()
            self.push_count -= 1
        else:
            raise Exception("Cannot pop from an empty stack!")

    def can_pop(self):
        return self.push_count > 0

    def add(self, *args):
        return self.solver.add(*args)

    def check(self):
        return self.solver.check()


def initGlobalVars():
    # Initialize global variables
    global solver
    # Z3 solver
    solver = CustomSolver(global_params.PARALLEL, global_params.TIMEOUT)

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

    global visited_edges_type
    visited_edges_type = {}

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

    global var_to_source
    var_to_source = {}


def run_build_cfg_and_analyze(target_params):
    initGlobalVars()
    build_cfg_and_analyze(target_params)
    print(result)


def build_cfg_and_analyze(target_params):
    targeted_sym_exec(target_params)
    generate_dot_file(target_params.funcSign)


def targeted_sym_exec(target_params):
    global blocks
    # executing, starting from beginning
    path_conditions_and_vars = {"path_condition": []}
    global_state = get_init_global_state(path_conditions_and_vars)
    analysis = init_analysis()
    params = Parameter(
        path_conditions_and_vars=path_conditions_and_vars,
        global_state=global_state,
        analysis=analysis,
        target_params=target_params,
    )
    # mark the start block of the targeted function and begin SE
    return sym_exec_block(
        params, target_params.target_block, blocks["0x0"], 0, -1, "fallback"
    )


def sym_exec_block(params, block, pre_block, depth, func_call, current_func_name):
    global solver
    global visited_edges
    global path_conditions
    global global_problematic_pcs
    global all_gs
    global results
    print()
    print("==============================")
    print(block.ident)

    visited = params.visited
    # in fact, no use of stack
    stack = params.stack
    mem = params.mem
    memory = params.memory
    global_state = params.global_state
    sha3_list = params.sha3_list
    path_conditions_and_vars = params.path_conditions_and_vars
    analysis = params.analysis
    calls = params.calls

    Edge = namedtuple("Edge", ["v1", "v2"])

    if block.return_private_from != None:
        pre_block = block.return_private_from

    elif block.private_call_from != None:
        pre_block = block.private_call_from

    current_edge = Edge(pre_block, block)

    if block.return_private_from != None:
        visited_edges_type[current_edge] = "private_call_return"

    elif block.private_call_from != None:
        visited_edges_type[current_edge] = "private_call_from"

    else:
        visited_edges_type[current_edge] = "normal"

    if current_edge in visited_edges:
        updated_count_number = visited_edges[current_edge] + 1
        visited_edges.update({current_edge: updated_count_number})
    else:
        visited_edges.update({current_edge: 1})

    # print(current_edge[0].ident)
    # print(current_edge[1].ident)
    # print("count number: " + str(visited_edges[current_edge]))

    if visited_edges[current_edge] > global_params.LOOP_LIMIT:
        log.debug("Overcome a number of loop limit. Terminating this path ...")
        print("Overcome a number of loop limit. Terminating this path ...")
        return stack

    # print(block)
    # statement[1] = op
    # se every statement in the block
    for statement in block.statements:
        # 'Statement', ['ident', 'op', 'operands', 'defs']
        sym_exec_ins(params, block, statement, func_call, current_func_name)

    visited.append(block)
    depth += 1

    # successors can only be 0 or 1 or 2 or 3
    # CALLPRIVATE opcode can insert the successors to make it 3
    successors = block.successors
    # if find privatecall, first SE the called private function
    if block.private_call_target != None:
        successor = block.private_call_target
        new_params = params.copy()
        sym_exec_block(
            new_params, successor, block, depth, func_call, current_func_name
        )

    elif block.return_private_target != None:
        successor = block.return_private_target
        new_params = params.copy()
        sym_exec_block(
            new_params, successor, block, depth, func_call, current_func_name
        )
    # end block or out of depth
    elif depth > global_params.DEPTH_LIMIT:
        print("Overcome a number of depth limit. Terminating this path ...")

    elif len(successors) == 0:
        print("TERMINATING A PATH ...")

    elif len(successors) == 1:
        # unconditional jump opcode
        successor = block.successors[0]
        new_params = params.copy()
        sym_exec_block(
            new_params, successor, block, depth, func_call, current_func_name
        )

    elif len(successors) == 2:
        # conditional jump
        branch_expression = block.get_branch_expression()
        solver.push()  # SET A BOUNDARY FOR SOLVER
        solver.add(branch_expression)

        try:
            if solver.check() == unsat:
                log.debug("INFEASIBLE PATH DETECTED")
                # print("======JUMPI jump target======")
                # print("INFEASIBLE PATH DETECTED")
                # print(block.ident)
            else:
                # true branch
                left_branch = block.get_jump_target()
                new_params = params.copy()
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
            traceback.print_exc()

        if solver.can_pop():
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
                # print("======JUMPI fall target======")
                # print("INFEASIBLE PATH DETECTED")
                # print(block.ident)
            else:
                right_branch = block.get_falls_to()
                new_params = params.copy()
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
            traceback.print_exc()
        if solver.can_pop():
            solver.pop()  # POP SOLVER CONTEXT
        # updated_count_number = visited_edges[current_edge] - 1
        # visited_edges.update({current_edge: updated_count_number})

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
    global path
    global result

    stack = params.stack
    mem = params.mem
    memory = params.memory
    global_state = params.global_state
    sha3_list = params.sha3_list
    path_conditions_and_vars = params.path_conditions_and_vars
    analysis = params.analysis
    calls = params.calls
    overflow_pcs = params.overflow_pcs
    # find recovered defs and uses from the decompiled IR
    defs, uses = emit_stmt(path, statement)
    # pass the stored states
    var_to_source = params.var_to_source
    target_params = params.target_params

    # print(target_params.fund_transfer_info)
    # hex value tranformed to int type (base 10)
    # var remain to strings

    # no need to care about const
    # its gonna be used in opcodes with real meaning

    instr = statement[1]
    ident = statement[0]

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
    print("------------------------------")
    print("EXECUTING: " + instr)
    print(defs)
    print(uses)
    # print(block.ident)
    # print(instr)
    if opcode == "STOP":
        return
    elif opcode == "ADD":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        # Type conversion is needed when they are mismatched
        if isReal(first) and isSymbolic(second):
            first = BitVecVal(first, 256)
            computed = first + second
        elif isSymbolic(first) and isReal(second):
            second = BitVecVal(second, 256)
            computed = first + second
        elif isSymbolic(first) and isSymbolic(second):
            computed = first + second
        else:
            # both are real and we need to manually modulus with 2 ** 256
            # if both are symbolic z3 takes care of modulus automatically
            computed = (first + second) % (2**256)
        computed = simplify(computed) if is_expr(computed) else computed

        # if not isAllReal(computed, first):
        #     solver.push()
        #     solver.add(UGT(first, computed))
        #     if check_sat(solver) == sat:
        #         global_problematic_pcs['integer_overflow'].append(
        #             Overflow(global_state['pc'] - 1, solver.model())
        #         )
        #         overflow_pcs.append(global_state['pc'] - 1)
        #     solver.pop()
        var_to_source[defs[0]] = computed

    elif opcode == "MUL":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        if isReal(first) and isSymbolic(second):
            first = BitVecVal(first, 256)
        elif isSymbolic(first) and isReal(second):
            second = BitVecVal(second, 256)
        computed = first * second & UNSIGNED_BOUND_NUMBER
        computed = simplify(computed) if is_expr(computed) else computed
        var_to_source[defs[0]] = computed

    elif opcode == "SUB":
        if isReal(defs[0]):
            return
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        if isReal(first) and isSymbolic(second):
            first = BitVecVal(first, 256)
            computed = first - second
        elif isSymbolic(first) and isReal(second):
            second = BitVecVal(second, 256)
            computed = first - second
        else:
            computed = (first - second) % (2**256)
        computed = simplify(computed) if is_expr(computed) else computed

        # if not isAllReal(first, second):
        #     solver.push()
        #     solver.add(UGT(second, first))
        #     if check_sat(solver) == sat:
        #         global_problematic_pcs['integer_underflow'].append(
        #             Underflow(global_state['pc'] - 1, solver.model())
        #         )
        #     solver.pop()
        var_to_source[defs[0]] = computed

    # due to the exist of PHI opcode, some path may not be feasible to perform DIV operation
    elif opcode == "DIV":
        print(var_to_source)
        # print(len(var_to_source.keys()))
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        # print(f"First: {first}")
        # print(f"Second: {second}")
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
            print(f"First: {first}, Type of First: {type(first)}")
            print(f"Second: {second}, Type of Second: {type(second)}")
            # solver.push()
            # solver.add(Not(second == 0))
            # print("Solver: ")
            # print(solver)
            # if check_sat(solver) == unsat or unknown:
            # computed = 0
            # else:
            # if UDIV Phase failed, may cause by the phi return
            computed = UDiv(first, second)
            # solver.pop()
        computed = simplify(computed) if is_expr(computed) else computed
        print("Computed:")
        print(computed)
        var_to_source[defs[0]] = computed

    elif opcode == "SDIV":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
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
        var_to_source[defs[0]] = computed

    elif opcode == "MOD":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
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
        var_to_source[defs[0]] = computed

    elif opcode == "SMOD":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
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
        var_to_source[defs[0]] = computed

    elif opcode == "ADDMOD":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        third = var_to_source[uses[2]] if uses[2] in var_to_source.keys() else uses[2]

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
        var_to_source[defs[0]] = computed

    elif opcode == "MULMOD":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        third = var_to_source[uses[2]] if uses[2] in var_to_source.keys() else uses[2]

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
        var_to_source[defs[0]] = computed

    elif opcode == "EXP":
        if isReal(defs[0]):
            pass
        else:
            base = (
                var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
            )
            exponent = (
                var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
            )
            if isAllReal(base, exponent):
                computed = pow(base, exponent, 2**256)
            else:
                # The computed value is unknown, this is because power is
                # not supported in bit-vector theory
                new_var_name = gen.gen_arbitrary_var()
                computed = BitVec(new_var_name, 256)
            computed = simplify(computed) if is_expr(computed) else computed
            var_to_source[defs[0]] = computed

    elif opcode == "SIGNEXTEND":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
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
        var_to_source[defs[0]] = computed
    #
    #  10s: Comparison and Bitwise Logic Operations
    #
    elif opcode == "LT":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        if isAllReal(first, second):
            first = to_unsigned(first)
            second = to_unsigned(second)
            if first < second:
                computed = 1
            else:
                computed = 0
        else:
            print(var_to_source)
            print(f"First: {first}, Type of First: {type(first)}")
            print(f"Second: {second}, Type of Second: {type(second)}")
            # miss cases due to PHI opcode
            if isinstance(first, str):
                first = BitVec(first, 256)
            elif isinstance(second, str):
                second = BitVec(second, 256)
            computed = If(ULT(first, second), BitVecVal(1, 256), BitVecVal(0, 256))
        computed = simplify(computed) if is_expr(computed) else computed
        print("Computed:")
        print(computed)
        var_to_source[defs[0]] = computed

    elif opcode == "GT":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]

        if isAllReal(first, second):
            first = to_unsigned(first)
            second = to_unsigned(second)
            if first > second:
                computed = 1
            else:
                computed = 0
        else:
            # print("GT===")
            # print(first)
            # print(second)
            computed = If(UGT(first, second), BitVecVal(1, 256), BitVecVal(0, 256))
        computed = simplify(computed) if is_expr(computed) else computed

        var_to_source[defs[0]] = computed

    elif opcode == "SLT":  # Not fully faithful to signed comparison
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]

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
        var_to_source[defs[0]] = computed

    elif opcode == "SGT":  # Not fully faithful to signed comparison
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
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
        var_to_source[defs[0]] = computed

    elif opcode == "EQ":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        if isAllReal(first, second):
            if first == second:
                computed = 1
            else:
                computed = 0
        else:
            computed = If(first == second, BitVecVal(1, 256), BitVecVal(0, 256))
        computed = simplify(computed) if is_expr(computed) else computed
        var_to_source[defs[0]] = computed
    elif opcode == "ISZERO":
        # Tricky: this instruction works on both boolean and integer,
        # when we have a symbolic expression, type error might occur
        # Currently handled by try and catch

        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        if isReal(first):
            if first == 0:
                computed = 1
            else:
                computed = 0
        else:
            computed = If(first == 0, BitVecVal(1, 256), BitVecVal(0, 256))
        print(computed)
        computed = simplify(computed) if is_expr(computed) else computed
        var_to_source[defs[0]] = computed
    elif opcode == "AND":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        computed = first & second
        computed = simplify(computed) if is_expr(computed) else computed
        var_to_source[defs[0]] = computed

    elif opcode == "OR":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]

        computed = first | second
        computed = simplify(computed) if is_expr(computed) else computed
        var_to_source[defs[0]] = computed

    elif opcode == "XOR":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]

        computed = first ^ second
        computed = simplify(computed) if is_expr(computed) else computed
        var_to_source[defs[0]] = computed

    elif opcode == "NOT":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        computed = (~first) & UNSIGNED_BOUND_NUMBER
        computed = simplify(computed) if is_expr(computed) else computed
        var_to_source[defs[0]] = computed

    # model IR special op code PHI
    # dataflow symbol opcode
    elif opcode == "PHI":
        flow_from = (
            var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        )
        flow_to = defs[0]
        var_to_source[flow_to] = flow_from

    elif opcode == "BYTE":
        first = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        byte_index = 32 - first - 1
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]

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
        var_to_source[defs[0]] = computed

    #
    # 20s: SHA3/KECCAK256
    #
    elif opcode in ["KECCAK256", "SHA3"]:
        s0 = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        s1 = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        # s0 = uses[0]  # 0
        # s1 = uses[1]  # 64
        slot = None
        if isAllReal(s0, s1):
            # simulate the hashing of sha3
            data = [str(x) for x in memory[s0 : s0 + s1]]

            # *Slot id in memory[63] <= MSTORE(64, slot)
            slot = memory[63]
            # print(slot)
            # print(sha3_list)
            position = "".join(data)
            position = re.sub("[\s+]", "", position)
            position = zlib.compress(six.b(position), 9)
            position = base64.b64encode(position)
            position = position.decode("utf-8", "strict")
            if position in sha3_list:
                var_to_source[defs[0]] = sha3_list[position]
            else:
                new_var_name = gen.gen_arbitrary_var()
                new_var = BitVec(new_var_name, 256)
                sha3_list[position] = new_var
                var_to_source[defs[0]] = new_var
        else:
            # push into the execution a fresh symbolic variable
            new_var_name = gen.gen_arbitrary_var()
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
            var_to_source[defs[0]] = new_var
    #
    # 30s: Environment Information
    #
    elif opcode == "ADDRESS":  # get address of currently executing account
        var_to_source[defs[0]] = path_conditions_and_vars["Ia"]
    elif opcode == "BALANCE":
        address = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]

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
        var_to_source[defs[0]] = new_var

    elif opcode == "CALLER":  # get caller address
        # that is directly responsible for this execution
        var_to_source[defs[0]] = global_state["sender_address"]
    elif opcode == "ORIGIN":  # get execution origination address
        var_to_source[defs[0]] = global_state["origin"]
    elif opcode == "CALLVALUE":  # get value of this transaction
        var_to_source[defs[0]] = global_state["value"]
        # buy function feature: msg.value to transfer the token
    elif opcode == "CALLDATALOAD":  # from inputter data from environment
        position = (
            var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        )
        new_var_name = gen.gen_data_var(position)
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        var_to_source[defs[0]] = new_var

    elif opcode == "CALLDATASIZE":
        new_var_name = gen.gen_data_size()
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        var_to_source[defs[0]] = new_var
    elif opcode == "CALLDATACOPY":  # Copy inputter data to memory
        #  TODO: Don't know how to simulate this yet
        pass
    # elif opcode == "CODESIZE":
    #     if g_disasm_file.endswith(".disasm"):
    #         evm_file_name = g_disasm_file[:-7]
    #     else:
    #         evm_file_name = g_disasm_file
    #     with open(evm_file_name, "r") as evm_file:
    #         evm = evm_file.read()[:-1]
    #         code_size = len(evm) / 2
    #         var_to_source[defs[0]] = code_size
    # elif opcode == "CODECOPY":
    #     mem_location = (
    #         var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
    #     )
    #     code_from = (
    #         var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
    #     )
    #     no_bytes = (
    #         var_to_source[uses[2]] if uses[2] in var_to_source.keys() else uses[2]
    #     )
    #     current_miu_i = global_state["miu_i"]

    #     if isAllReal(mem_location, current_miu_i, code_from, no_bytes):
    #         temp = int(math.ceil((mem_location + no_bytes) / float(32)))
    #         if temp > current_miu_i:
    #             current_miu_i = temp

    #         if g_disasm_file.endswith(".disasm"):
    #             evm_file_name = g_disasm_file[:-7]
    #         else:
    #             evm_file_name = g_disasm_file
    #         with open(evm_file_name, "r") as evm_file:
    #             evm = evm_file.read()[:-1]
    #             start = code_from * 2
    #             end = start + no_bytes * 2
    #             code = evm[start:end]
    #         mem[mem_location] = int(code, 16)
    #     else:
    #         new_var_name = gen.gen_code_var("Ia", code_from, no_bytes)
    #         if new_var_name in path_conditions_and_vars:
    #             new_var = path_conditions_and_vars[new_var_name]
    #         else:
    #             new_var = BitVec(new_var_name, 256)
    #             path_conditions_and_vars[new_var_name] = new_var

    #         temp = ((mem_location + no_bytes) / 32) + 1
    #         current_miu_i = to_symbolic(current_miu_i)
    #         expression = current_miu_i < temp
    #         solver.push()
    #         solver.add(expression)
    #         if MSIZE:
    #             if check_sat(solver) != unsat:
    #                 current_miu_i = If(expression, temp, current_miu_i)
    #         solver.pop()
    #         mem.clear()  # very conservative
    #         mem[str(mem_location)] = new_var
    #     global_state["miu_i"] = current_miu_i

    elif opcode == "RETURNDATACOPY":
        pass
    elif opcode == "RETURNDATASIZE":
        new_var_name = gen.gen_arbitrary_var()
        new_var = BitVec(new_var_name, 256)
        var_to_source[defs[0]] = new_var
    elif opcode == "GASPRICE":
        var_to_source[defs[0]] = global_state["gas_price"]
    elif opcode == "EXTCODESIZE":
        address = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]

        # not handled yet
        new_var_name = gen.gen_code_size_var(address)
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        var_to_source[defs[0]] = new_var

    elif opcode == "EXTCODECOPY":
        address = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        mem_location = (
            var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        )
        code_from = (
            var_to_source[uses[2]] if uses[2] in var_to_source.keys() else uses[2]
        )
        no_bytes = (
            var_to_source[uses[3]] if uses[3] in var_to_source.keys() else uses[3]
        )
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
    #
    #  40s: Block Information
    #
    elif opcode == "BLOCKHASH":  # information from block header
        new_var_name = "IH_blockhash"
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        var_to_source[defs[0]] = new_var

    elif opcode == "COINBASE":  # information from block header
        var_to_source[defs[0]] = global_state["currentCoinbase"]
    elif opcode == "TIMESTAMP":  # information from block header
        var_to_source[defs[0]] = global_state["currentTimestamp"]
    elif opcode == "NUMBER":  # information from block header
        var_to_source[defs[0]] = global_state["currentNumber"]
    elif opcode == "DIFFICULTY":  # information from block header
        var_to_source[defs[0]] = global_state["currentDifficulty"]
    elif opcode == "GASLIMIT":  # information from block header
        var_to_source[defs[0]] = global_state["currentGasLimit"]
    #
    #  50s: Stack, Memory, Storage, and Flow Information
    #
    elif opcode == "POP":
        pass
    elif opcode == "MLOAD":
        address = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        print(address)
        print(mem)
        current_miu_i = global_state["miu_i"]
        if isAllReal(address, current_miu_i) and address in mem:
            temp = int(math.ceil((address + 32) / float(32)))
            if temp > current_miu_i:
                current_miu_i = temp
            value = mem[address]
            var_to_source[defs[0]] = value
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
            var_to_source[defs[0]] = new_var
            if isReal(address):
                mem[address] = new_var
            else:
                mem[str(address)] = new_var
        global_state["miu_i"] = current_miu_i

    elif opcode == "MSTORE":
        stored_address = (
            var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        )

        stored_value = (
            var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        )
        # MSTORE slotid to MEM32
        print(stored_address)
        print(stored_value)
        print(mem)
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
    elif opcode == "MSTORE8":
        stored_address = (
            var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        )
        temp_value = (
            var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        )
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
    elif opcode == "SLOAD":
        position = (
            var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        )

        if isReal(position) and position in global_state["Ia"]:
            value = global_state["Ia"][position]
            var_to_source[defs[0]] = value
        else:
            if str(position) in global_state["Ia"]:
                value = global_state["Ia"][str(position)]
                var_to_source[defs[0]] = value
            else:
                if is_expr(position):
                    position = simplify(position)
                new_var_name = (
                    gen.gen_owner_store_var(var_to_source[position])
                    if position in var_to_source.keys()
                    else gen.gen_owner_store_var(position)
                )

                if new_var_name in path_conditions_and_vars:
                    new_var = path_conditions_and_vars[new_var_name]
                else:
                    new_var = BitVec(new_var_name, 256)
                    path_conditions_and_vars[new_var_name] = new_var
                # stack.insert(0, new_var)
                var_to_source[defs[0]] = new_var
                if isReal(position):
                    global_state["Ia"][position] = new_var
                else:
                    global_state["Ia"][str(position)] = new_var

    elif opcode == "SSTORE":
        stored_address = (
            var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        )
        stored_value = (
            var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        )
        logging.info("SSTORE")

        if isReal(stored_address):
            # note that the stored_value could be unknown
            global_state["Ia"][stored_address] = stored_value
            print(hex(stored_address))
            # check time sstore op
            print(target_params.state_dependency_info.time[target_params.funcSign])
            if (
                hex(stored_address)
                in target_params.state_dependency_info.time[target_params.funcSign]
            ):
                result["lock"] = True

            # check supply sstore op
            # the supply and balance slot exist in the same func
            # supply dependant on owner
            if (
                hex(stored_address)
                in target_params.state_dependency_info.supply[target_params.funcSign]
                and target_params.funcSign
                in target_params.state_dependency_info.owner.keys()
            ):
                # check owner constrain
                if (
                    hex(stored_address)
                    in target_params.state_dependency_info.slot_dependency_map.keys()
                ):
                    result["mint"] = True

            # check pause sstore op
            if (
                hex(stored_address)
                in target_params.state_dependency_info.pause[target_params.funcSign]
            ):
                # default has owner constrain
                result["pause"] = True
        else:
            # note that the stored_value could be unknown
            global_state["Ia"][str(stored_address)] = stored_value

    elif opcode == "JUMP":
        # know jump target in the successors identified (length = 1)
        target_block = uses[0]
        # print(block.successors[0].ident)

    elif opcode == "JUMPI":
        # We need to prepare two branches
        target_address = uses[0]
        # print(hex(target_address))

        for successor in block.successors:
            if successor.ident.startswith(hex(target_address)):
                block.set_jump_target(successor)
            else:
                block.set_falls_to(successor)
        # print(block.get_jump_target().ident)
        # print(block.get_falls_to().ident)
        flag = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        branch_expression = BitVecVal(0, 1) == BitVecVal(1, 1)
        if isReal(flag):
            if flag != 0:
                branch_expression = True
        else:
            branch_expression = flag != 0
        block.set_branch_expression(branch_expression)

    elif opcode == "PC":
        return
    elif opcode == "MSIZE":
        msize = 32 * global_state["miu_i"]
        var_to_source[defs[0]] = msize
    elif opcode == "GAS":
        # In general, we do not have this precisely. It depends on both
        # the initial gas and the amount has been depleted
        # we need o think about this in the future, in case precise gas
        # can be tracked
        new_var_name = gen.gen_gas_var()
        new_var = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = new_var
        var_to_source[defs[0]] = new_var
    elif opcode == "JUMPDEST":
        # Literally do nothing
        pass
    #
    #  60s & 70s: Push Operations
    #  No push op in gigahorse IR
    elif opcode.startswith("PUSH", 0):  # this is a push instruction
        pass

    elif opcode == "CONST":
        # push constants but used in real ops
        pass
    #
    #  80s: Duplication Operations
    #
    elif opcode.startswith("DUP", 0):
        # in fact no use of DUP
        pass

    #
    #  90s: Swap Operations
    #
    elif opcode.startswith("SWAP", 0):
        # in fact no use of SWAP
        pass

    #
    #  a0s: Logging Operations
    #
    elif opcode in ("LOG0", "LOG1", "LOG2", "LOG3", "LOG4"):
        pass

    #
    #  f0s: System Operations
    #
    elif opcode in ["CREATE", "CREATE2"]:
        new_var_name = gen.gen_arbitrary_var()
        new_var = BitVec(new_var_name, 256)
        var_to_source[defs[0]] = new_var

    elif opcode == "CALL":
        # TODO: Need to handle miu_i
        outgas = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        recipient = (
            var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        )
        transfer_amount = (
            var_to_source[uses[2]] if uses[2] in var_to_source.keys() else uses[2]
        )
        start_data_input = (
            var_to_source[uses[3]] if uses[3] in var_to_source.keys() else uses[3]
        )
        size_data_input = (
            var_to_source[uses[4]] if uses[4] in var_to_source.keys() else uses[4]
        )
        start_data_output = (
            var_to_source[uses[5]] if uses[5] in var_to_source.keys() else uses[5]
        )
        size_data_ouput = (
            var_to_source[uses[6]] if uses[6] in var_to_source.keys() else uses[6]
        )
        log.info(recipient)
        log.info(transfer_amount)
        # print(recipient)
        # print(transfer_amount)
        print(ident)
        # feasibility forward check
        # get the formula of the transfer amount
        # with the inferred transfer recipient role
        if ident in target_params.fund_transfer_info.calls.keys():
            res = [
                target_params.fund_transfer_info.calls[ident],
                target_params.fund_transfer_info.recipient_role[ident],
            ]
            if target_params.fund_transfer_info.recipient_role[ident] == "NORMAL":
                result["tax"][ident] = res
            else:  # user transfer
                result["transfer"][ident] = res
            if target_params.fund_transfer_info.recipient_role[ident] == "OWNER":
                result["clear"][ident] = res

        # in the paper, it is shaky when the size of data output is
        # min of stack[6] and the | o |

        if isReal(transfer_amount):
            if transfer_amount == 0:
                # stack.insert(0, 1)  # x = 0
                return

        # Let us ignore the call depth
        balance_ia = global_state["balance"]["Ia"]
        is_enough_fund = transfer_amount <= balance_ia
        solver.push()
        solver.add(is_enough_fund)

        if check_sat(solver) == unsat:
            # this means not enough fund, thus the execution will result in exception
            solver.pop()
            var_to_source[defs[0]] = 0
            # stack.insert(0, 0)  # x = 0
        else:
            # the execution is possibly okay
            var_to_source[defs[0]] = 1
            # stack.insert(0, 1)  # x = 1
            solver.pop()
            solver.add(is_enough_fund)
            path_conditions_and_vars["path_condition"].append(is_enough_fund)
            last_idx = len(path_conditions_and_vars["path_condition"]) - 1
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

    elif opcode == "CALLCODE":
        # TODO: Need to handle miu_i
        outgas = var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        recipient = (
            var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        )  # this is not used as recipient

        transfer_amount = (
            var_to_source[uses[2]] if uses[2] in var_to_source.keys() else uses[2]
        )
        start_data_input = (
            var_to_source[uses[3]] if uses[3] in var_to_source.keys() else uses[3]
        )
        size_data_input = (
            var_to_source[uses[4]] if uses[4] in var_to_source.keys() else uses[4]
        )
        start_data_output = (
            var_to_source[uses[5]] if uses[5] in var_to_source.keys() else uses[5]
        )
        size_data_ouput = (
            var_to_source[uses[6]] if uses[6] in var_to_source.keys() else uses[6]
        )
        # in the paper, it is shaky when the size of data output is
        # min of stack[6] and the | o |

        if isReal(transfer_amount):
            if transfer_amount == 0:
                # stack.insert(0, 1)  # x = 0
                var_to_source[defs[0]] = 1
                return

        # Let us ignore the call depth
        balance_ia = global_state["balance"]["Ia"]
        is_enough_fund = transfer_amount <= balance_ia
        solver.push()
        solver.add(is_enough_fund)

        if check_sat(solver) == unsat:
            # this means not enough fund, thus the execution will result in exception
            solver.pop()
            var_to_source[defs[0]] = 0
            # stack.insert(0, 0)  # x = 0
        else:
            # the execution is possibly okay
            var_to_source[defs[0]] = 1
            # stack.insert(0, 1)  # x = 1
            solver.pop()
            solver.add(is_enough_fund)
            path_conditions_and_vars["path_condition"].append(is_enough_fund)
            last_idx = len(path_conditions_and_vars["path_condition"]) - 1

    elif opcode in ("DELEGATECALL", "STATICCALL"):
        recipient = (
            var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        )

        new_var_name = gen.gen_arbitrary_var()
        new_var = BitVec(new_var_name, 256)
        var_to_source[defs[0]] = new_var

    elif opcode == "REVERT":
        pass
    elif opcode == "RETURN":
        # TODO: Need to handle miu_i
        pass

    elif opcode in ("SELFDESTRUCT", "SUICIDE"):
        recipient = (
            var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        )
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
        # *For selector to shift left 224 bits
        # EXP
        base = 2
        exponent = (
            var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        )
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
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        if isReal(first) and isSymbolic(second):
            first = BitVecVal(first, 256)
        elif isSymbolic(first) and isReal(second):
            second = BitVecVal(second, 256)
        computed = first * second & UNSIGNED_BOUND_NUMBER
        computed = simplify(computed) if is_expr(computed) else computed
        var_to_source[defs[0]] = computed

    elif opcode == "SHR":
        # EXP
        base = 2
        exponent = (
            var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        )
        # Type conversion is needed when they are mismatched
        if isAllReal(base, exponent):
            computed = pow(base, exponent, 2**256)
        else:
            # The computed value is unknown, this is because power is
            # not supported in bit-vector theory
            new_var_name = gen.gen_arbitrary_var()
            computed = BitVec(new_var_name, 256)
        computed = simplify(computed) if is_expr(computed) else computed

        # DIV
        first = computed
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
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
        var_to_source[defs[0]] = computed

    elif opcode == "SAR":
        # EXP
        base = 2
        exponent = (
            var_to_source[uses[0]] if uses[0] in var_to_source.keys() else uses[0]
        )
        # Type conversion is needed when they are mismatched
        if isAllReal(base, exponent):
            computed = pow(base, exponent, 2**256)
        else:
            # The computed value is unknown, this is because power is
            # not supported in bit-vector theory
            new_var_name = gen.gen_arbitrary_var()
            computed = BitVec(new_var_name, 256)
        computed = simplify(computed) if is_expr(computed) else computed

        # not equivalent to SDIV
        first = computed
        second = var_to_source[uses[1]] if uses[1] in var_to_source.keys() else uses[1]
        if isAllReal(first, second):
            first = to_unsigned(first)
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

                    def z3_abs(x):
                        return If(x >= 0, x, -x)

                    first = z3_abs(first)
                    second = z3_abs(second)
                    computed = sign * (first / second)
                    solver.pop()
                solver.pop()
            solver.pop()
        computed = simplify(computed) if is_expr(computed) else computed
        var_to_source[defs[0]] = computed

    elif opcode == "SELFBALANCE":
        # address(this).balance
        var_to_source[defs[0]] = global_state["currentSelfBalance"]

    elif opcode == "CHAINID":
        # chain_id = {  1 // mainnet
        #    {  2 // Morden testnet (disused)
        #    {  2 // Expanse mainnet
        #    {  3 // Ropsten testnet
        #    {  4 // Rinkeby testnet
        #    {  5 // Goerli testnet
        #    { 42 // Kovan testnet
        #    { ...
        var_to_source[defs[0]] = global_state["currentChainId"]

    elif opcode == "BASEFEE":
        var_to_source[defs[0]] = global_state["currentBaseFee"]

    elif opcode == "CALLPRIVATE":
        # todomark start block, find its func, when executing returnprivate in this func, find the return target
        private_fun_start_block = blocks[hex(uses[0])]
        # print(private_fun_start_block.ident)
        target_private_fun = tac_block_function[private_fun_start_block.ident]
        functions[target_private_fun].return_defs = defs
        functions[target_private_fun].caller_block = block
        block.private_call_target = private_fun_start_block
        block.private_call_target.private_call_from = block
        for i in range(1, len(uses)):
            if uses[i] in var_to_source.keys():
                uses[i] = var_to_source[uses[i]]
            elif isinstance(uses[i], str):
                uses[i] = BitVec(uses[i], 256)
            var_to_source[hex(uses[0]).replace("0x", "v") + "arg" + str(i - 1)] = uses[
                i
            ]

    elif opcode == "RETURNPRIVATE":
        # should not use the return arg as the return target
        # should use the successor of the caller function
        return_defs = functions[tac_block_function[block.ident]].return_defs
        # print(return_defs)
        block.return_private_target = functions[
            tac_block_function[block.ident]
        ].caller_block.successors[0]
        # print(block.return_private_target.ident)
        block.return_private_target.return_private_from = block
        for i in range(1, len(uses)):
            var_to_source[return_defs[i - 1]] = var_to_source[uses[i]]
    elif opcode == "THROW":
        pass
    else:
        print("UNKNOWN INSTRUCTION: " + opcode)
        log.info("UNKNOWN INSTRUCTION: " + opcode)
    # print(var_to_source)
    # print(mem)


def analyze(target_params):
    run_build_cfg_and_analyze(target_params)


def run(inputs):
    global results
    global funcs_to_be_checked
    global blocks
    global functions
    global tac_block_function
    global fund_transfer_graph
    global state_dependency_graph
    global func_map
    global path

    blocks = inputs["blocks"]
    functions = inputs["functions"]
    tac_block_function = inputs["tac_block_function"]
    funcs_to_be_checked = inputs["funcs_to_be_checked"]
    fund_transfer_graph = inputs['fund_transfer_graph']
    state_dependency_graph = inputs["state_dependency_graph"]
    func_map = inputs["func_map"]
    path = inputs["path"]

    log.info("\t============ Results ===========")
    # init params for target SE
    # should note: target functions (head blocks), critical slots and dependency relationship
    # self.funcs_to_be_checked = ["0xdd467064"]
    processes = []

    for funcSign in funcs_to_be_checked:
        target_params = TargetedParameters(
            path=path,
            funcSign=funcSign,
            fund_transfer_info=fund_transfer_graph,
            target_block=functions[func_map[funcSign]].head_block,
            state_dependency_info=state_dependency_graph,
        )

        process = Process(target=analyze, args=(target_params,))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()
    # run_build_cfg_and_analyze(target_params)
    # print("======================END=====================")
    print("======================END=====================")
    return results, 0
    # afterward analysis
    # could be parallel for multithread SE process
    # run_build_cfg_and_analyze(target_params)

    # several keys to be checked during SE
    # 1. feasibility of the key statement
    # 2. exact value of transfer amount
    # 3. owner dependency check (authority check)
    analyze()
    # ret = detect_vulnerabilities()
    # closing_message()
    return {}, 0
