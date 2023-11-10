from z3 import *


class CustomSolver:
    def __init__(self, parallel=0):
        self.push_count = 0
        if parallel == 1:
            t2 = Then('simplify', 'solve-eqs', 'smt')
            _t = Then('tseitin-cnf-core', 'split-clause')
            t1 = ParThen(_t, t2)
            self.solver = OrElse(t1, t2).solver()
        else:
            self.solver = Solver()
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

    def model(self):
        return self.solver.model()

    def can_pop(self):
        return self.push_count > 0

    def add(self, *args):
        return self.solver.add(*args)

    def check(self):
        return self.solver.check()


# 创建一个32位的位向量符号变量
Id_2 = BitVec('Id_2', 32)

# 定义您的表达式
expr = UDiv(UDiv(5 * Id_2, 100), 5)

# 创建求解器
s = CustomSolver()

# 添加约束将Id_2设为100
s.add(Id_2 == 100)

# 检查是否有解
if s.check() == sat:
    # 如果有解，获取模型并计算表达式的值
    m = s.model()
    print(m.eval(expr))
else:
    print("No solution")
