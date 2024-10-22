from typing import Tuple, List, Union, Mapping, Set
from collections import namedtuple, defaultdict
from itertools import chain

Statement = namedtuple('Statement', ['ident', 'op', 'operands', 'defs'])


class Block:
    def __init__(self, ident: str, statements: List[Statement]):
        self.ident = ident
        self.statements = statements
        self.predecessors: List[Block] = []
        self.successors: List[Block] = []
        self.private_call_target: Block = None
        self.return_private_target: Block = None
        # for edge link of privatecall
        self.return_private_from: Block = None
        self.private_call_from: Block = None

        self.jump_target: Block = None
        self.falls_to: Block = None

    def set_falls_to(self, block):
        self.falls_to = block

    def get_falls_to(self):
        return self.falls_to

    def set_jump_target(self, block):
        self.jump_target = -1

    def get_jump_target(self):
        return self.jump_target

    def set_branch_expression(self, branch):
        self.branch_expression = branch

    def get_branch_expression(self):
        return self.branch_expression

    def set_falls_to(self, block):
        self.falls_to = block

    def get_falls_to(self):
        return self.falls_to

    def set_jump_target(self, block):
        self.jump_target = block

    def get_jump_target(self):
        return self.jump_target


class Function:
    def __init__(
        self,
        ident: str,
        name: str,
        head_block: Block,
        is_public: bool,
        selector: str,
        formals: List[str],
    ):
        self.ident = ident
        self.name = name
        self.formals = formals
        self.is_public = is_public
        self.selector = selector
        self.head_block = head_block
        self.return_defs = []
        self.caller_block: Block = None


def load_csv(path: str, seperator: str = '\t') -> List[Union[str, List[str]]]:
    with open(path) as f:
        return [line.split(seperator) for line in f.read().splitlines()]


def load_csv_map(
    path: str, seperator: str = '\t', reverse: bool = False
) -> Mapping[str, str]:
    return (
        {y: x for x, y in load_csv(path, seperator)}
        if reverse
        else {x: y for x, y in load_csv(path, seperator)}
    )


def load_csv_multimap(
    path: str, seperator: str = '\t', reverse: bool = False
) -> Mapping[str, List[str]]:
    ret = defaultdict(list)

    if reverse:
        for y, x in load_csv(path, seperator):
            ret[x].append(y)
    else:
        for x, y in load_csv(path, seperator):
            ret[x].append(y)

    return ret


def construct_cfg(path) -> Tuple[Mapping[str, Block], Mapping[str, Function]]:
    # Load facts
    # (block, function)
    # map function to its blocks
    tac_function_blocks = load_csv_multimap(path + 'InFunction.csv', reverse=True)

    # map blocks to its function
    tac_block_function = load_csv_map(path + 'InFunction.csv')
    # print(tac_block_function)
    # (pubfuncid, selector)
    tac_func_id_to_public = load_csv_map(path + 'PublicFunction.csv')
    # function name, not necessary in SE
    tac_high_level_func_name = load_csv_map(path + 'HighLevelFunctionName.csv')

    tac_formal_args: Mapping[str, List[Tuple[str, int]]] = defaultdict(list)
    for func_id, arg, pos in load_csv(path + 'FormalArgs.csv'):
        tac_formal_args[func_id].append((arg, int(pos)))

    # Inverse mapping
    # global tac_block_function
    tac_block_function: Mapping[str, str] = {}
    for func_id, block_ids in tac_function_blocks.items():
        for block in block_ids:
            tac_block_function[block] = func_id
    tac_block_stmts = load_csv_multimap(path + 'TAC_Block.csv', reverse=True)
    tac_op = load_csv_map(path + 'TAC_Op.csv')

    # Load statement defs/uses
    tac_defs: Mapping[str, List[Tuple[str, int]]] = defaultdict(list)
    for stmt_id, var, pos in load_csv(path + 'TAC_Def.csv'):
        tac_defs[stmt_id].append((var, int(pos)))

    tac_uses: Mapping[str, List[Tuple[str, int]]] = defaultdict(list)
    for stmt_id, var, pos in load_csv(path + 'TAC_Use.csv'):
        tac_uses[stmt_id].append((var, int(pos)))

    # Load block edges
    tac_block_succ = load_csv_multimap(path + 'LocalBlockEdge.csv')
    tac_block_pred: Mapping[str, List[str]] = defaultdict(list)
    for block, succs in tac_block_succ.items():
        for succ in succs:
            tac_block_pred[succ].append(block)

    def stmt_sort_key(stmt_id: str) -> int:
        return int(stmt_id.replace("S", "").split('0x')[1].split('_')[0], base=16)

    # Construct blocks
    blocks: Mapping[str, Block] = {}
    for block_id in chain(*tac_function_blocks.values()):
        try:
            statements = [
                Statement(
                    s_id,
                    tac_op[s_id],
                    [var for var, _ in sorted(tac_uses[s_id], key=lambda x: x[1])],
                    [var for var, _ in sorted(tac_defs[s_id], key=lambda x: x[1])],
                )
                for s_id in sorted(tac_block_stmts[block_id], key=stmt_sort_key)
            ]
            blocks[block_id] = Block(block_id, statements)
        except:
            __import__('pdb').set_trace()

    # Link blocks together
    for block in blocks.values():
        block.predecessors = [blocks[pred] for pred in tac_block_pred[block.ident]]
        block.successors = [blocks[succ] for succ in tac_block_succ[block.ident]]

    functions: Mapping[str, Function] = {}
    for (block_id,) in load_csv(path + 'IRFunctionEntry.csv'):
        func_id = tac_block_function[block_id]

        high_level_name = (
            'fallback()'
            if tac_func_id_to_public.get(func_id, '_') == '0x0'
            else tac_high_level_func_name[func_id]
        )
        formals = [
            var for var, _ in sorted(tac_formal_args[func_id], key=lambda x: x[1])
        ]

        functions[func_id] = Function(
            func_id,
            high_level_name,
            blocks[block_id],
            func_id in tac_func_id_to_public or func_id == '0x0',
            "",
            formals,
        )

    return blocks, functions, tac_block_function


def emit_stmt(path, stmt: Statement):
    tac_variable_value = load_csv_map(path + 'TAC_Variable_Value.csv')

    def render_var(var: str):
        if var in tac_variable_value:
            return int(tac_variable_value[var], 16)
        else:
            return f"v{var.replace('0x', '')}"

    defs = [render_var(v) for v in stmt.defs]
    uses = [render_var(v) for v in stmt.operands]

    return defs, uses

    # if defs:
    #     emit(f"{stmt.ident}: {', '.join(defs)} = {stmt.op} {', '.join(uses)}", out, 1)
    # else:
    #     emit(f"{stmt.ident}: {stmt.op} {', '.join(uses)}", out, 1)
