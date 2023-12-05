import six
from z3 import *
from z3.z3util import get_vars


def ceil32(x):
    return x if x % 32 == 0 else x + 32 - (x % 32)


def isSymbolic(value):
    return not isinstance(value, six.integer_types)


def isReal(value):
    return isinstance(value, six.integer_types)


def isAllReal(*args):
    for element in args:
        if isSymbolic(element):
            return False
    return True


def to_symbolic(number):
    if isReal(number):
        return BitVecVal(number, 256)
    return number


def to_unsigned(number):
    if number < 0:
        return number + 2**256
    return number


def to_signed(number):
    if number > 2 ** (256 - 1):
        return (2 ** (256) - number) * (-1)
    else:
        return number


def check_sat(solver, pop_if_exception=True):
    try:
        ret = solver.check()
        if ret == unknown:
            # pop unknown
            solver.pop()
            return ret
            # raise Z3Exception(solver.reason_unknown())
    except Exception as e:
        if pop_if_exception:
            solver.pop()
        raise e
    return ret


def custom_deepcopy(input):
    output = {}
    for key in input:
        if isinstance(input[key], list):
            output[key] = list(input[key])
        elif isinstance(input[key], dict):
            output[key] = custom_deepcopy(input[key])
        else:
            output[key] = input[key]
    return output


def is_storage_var(var):
    if not isinstance(var, str):
        var = var.decl().name()
    return var.startswith("Ia_store")


def is_balance_var(var):
    if not is_expr(var):
        return False
    if not isinstance(var, str):
        var = var.decl().name()
    return var.startswith("balance_") or var == "IH_b"


def is_caller(var):
    if not is_expr(var):
        return False
    if not isinstance(var, str):
        var = var.decl().name()
    return var == "Is"


def is_zero(var):
    return str(var) == "0" or str(var) == "0.0"


def is_mem_var(var):
    if not is_expr(var):
        return False
    if not isinstance(var, str):
        var = var.decl().name()
    return var.startswith("mem_")


def is_env_var(var):
    if not is_expr(var):
        return False
    if not isinstance(var, str):
        var = var.decl().name()
    return var.startswith("IH_")


def contains_mul_or_div(expr):
    if not is_expr(expr):
        return False
    if is_const(expr):
        return False

    if expr.decl().kind() == Z3_OP_BMUL or expr.decl().kind() == Z3_OP_BUDIV_I:
        return True

    for child in expr.children():
        if contains_mul_or_div(child):
            return True

    return False


def is_subtracted_from_iv_or_balance(expr):
    if is_expr(expr) and expr.decl().kind() == Z3_OP_BADD:
        minuend = expr.arg(0)  # Get the first operand (minuend)
        if is_expr(minuend) and (
            minuend.decl().name() == "Iv" or is_balance_var(minuend.decl().name())
        ):
            return True
    return False


# copy only storage values/ variables from a given global state
# TODO: add balance in the future
def copy_global_values(global_state):
    return global_state["Ia"]


# check if a variable is in an expression
def is_in_expr(var, expr):
    list_vars = get_vars(expr)
    set_vars = set(i.decl().name() for i in list_vars)
    return var in set_vars


# check if an expression has any storage variables
def has_storage_vars(expr, storage_vars):
    list_vars = get_vars(expr)
    for var in list_vars:
        if var in storage_vars:
            return True
    return False


def get_all_vars(exprs):
    ret_vars = []
    for expr in exprs:
        if is_expr(expr):
            ret_vars += get_vars(expr)
    return ret_vars


def get_storage_position(var):
    if not isinstance(var, str):
        var = var.decl().name()
    pos = var.split("-")[1]
    try:
        return int(pos)
    except:
        return pos


def get_storage_var_name(var):
    if not isinstance(var, str):
        var = var.decl().name()
    pos = var.split("-")[2]
    return pos
    # try: return int(pos)
    # except: return pos


# Rename variables to distinguish variables in two different paths.
# e.g. Ia_store_0 in path i becomes Ia_store_0_old if Ia_store_0 is modified
# else we must keep Ia_store_0 if its not modified
def rename_vars(pcs, global_states):
    ret_pcs = []
    vars_mapping = {}

    for expr in pcs:
        if is_expr(expr):
            list_vars = get_vars(expr)
            for var in list_vars:
                if var in vars_mapping:
                    expr = substitute(expr, (var, vars_mapping[var]))
                    continue
                var_name = var.decl().name()
                # check if a var is global
                if is_storage_var(var):
                    pos = get_storage_position(var)
                    # if it is not modified then keep the previous name
                    if pos not in global_states:
                        continue
                # otherwise, change the name of the variable
                new_var_name = var_name + "_old"
                new_var = BitVec(new_var_name, 256)
                vars_mapping[var] = new_var
                expr = substitute(expr, (var, vars_mapping[var]))
        ret_pcs.append(expr)

    ret_gs = {}
    # replace variable in storage expression
    for storage_addr in global_states:
        expr = global_states[storage_addr]
        # z3 4.1 makes me add this line
        if is_expr(expr):
            list_vars = get_vars(expr)
            for var in list_vars:
                if var in vars_mapping:
                    expr = substitute(expr, (var, vars_mapping[var]))
                    continue
                var_name = var.decl().name()
                # check if a var is global
                if var_name.startswith("Ia_store_"):
                    position = int(var_name.split("_")[len(var_name.split("_")) - 1])
                    # if it is not modified
                    if position not in global_states:
                        continue
                # otherwise, change the name of the variable
                new_var_name = var_name + "_old"
                new_var = BitVec(new_var_name, 256)
                vars_mapping[var] = new_var
                expr = substitute(expr, (var, vars_mapping[var]))
        ret_gs[storage_addr] = expr

    return ret_pcs, ret_gs
