import re
import pandas as pd
import os


class FormulaAnalyzer:
    def __init__(self, address):
        self.address = address

    def analyze_formula(self):
        # Paths to csv files
        base_path = f"./gigahorse-toolchain/.temp/{self.address}/out/"
        sink_loc = base_path + "Hyperion_SensitiveCall.csv"
        ops = ['Add', 'Sub', 'Mul', 'Div']
        op_paths = {op: base_path + f"Hyperion_{op}.csv" for op in ops}

        # Initialize the dataframes
        dfs = {}
        for op, path in op_paths.items():
            if os.path.exists(path) and (os.path.getsize(path) > 0):
                dfs[op] = pd.read_csv(path, header=None, sep='\t')

        if os.path.exists(sink_loc) and (os.path.getsize(sink_loc) > 0):
            sink_df = pd.read_csv(sink_loc, header=None, sep='\t')
            sink_df.columns = ["callStmt", "recipient", "amount", "amountFrom"]
        else:
            return

        # Create a dictionary to store all variables
        variables = {}
        for op, df in dfs.items():
            self.populate_variables(df, variables, op)

        print(variables)
        # Extract the target sink site variable
        # sink_site_var = sink_df["ethAmount"].unique()[0]
        sink_site_var = "0x97aV0x518V0x21c"

        # Extract the initial variables (those possibly flowing into the sink site)
        initial_vars = sink_df[sink_df["amount"] == sink_site_var]["amountFrom"]

        # Find path from initial variables to the sink site var
        for initial_var in initial_vars:
            # path = self.find_path_to_sink(variables, initial_var, sink_site_var)
            path = self.find_longest_path(variables, initial_var)
            if path:
                formula = self.construct_formula_from_path(path, variables)
                print(
                    f"The formula for {sink_site_var} starting from {initial_var} is {formula}"
                )

    def populate_variables(self, df, variables, operation):
        for _, row in df.iterrows():
            a, b, c = str(row[0]), str(row[1]), str(row[2])
            op_dict = {'Add': '+', 'Sub': '-', 'Div': '/', 'Mul': '*'}
            variables[a] = (b, c, op_dict[operation])

    def find_path_to_sink(self, variables, start_var, sink_var):
        visited = set()
        stack = [(start_var, [start_var])]
        while stack:
            (vertex, path) = stack.pop()
            if vertex in visited:
                continue
            if vertex == sink_var:
                return path
            visited.add(vertex)
            for next_vertex in variables.get(vertex, ()):
                if next_vertex not in visited:
                    stack.append((next_vertex, path + [next_vertex]))
        return None

    def find_longest_path(self, variables, start_var):
        visited = set()
        stack = [(start_var, [start_var])]
        longest_path = []

        while stack:
            (vertex, path) = stack.pop()
            if vertex in visited:
                continue
            visited.add(vertex)
            if len(path) > len(longest_path):
                longest_path = path
            for next_vertex in variables.get(vertex, ()):
                if next_vertex not in visited:
                    stack.append((next_vertex, path + [next_vertex]))

        return longest_path

    def construct_formula_from_path(self, path, variables):
        if len(path) == 1:
            return path[0]
        formula = path[-1]
        for i in range(len(path) - 2, -1, -1):
            b, c, op = variables[path[i]]
            formula = formula.replace(
                b, f'({self.construct_formula_from_path([b], variables)})'
            )
            formula = formula.replace(
                c, f'({self.construct_formula_from_path([c], variables)})'
            )
            formula = re.sub(
                rf'\b{re.escape(b)}\b',
                f'({self.construct_formula_from_path([b], variables)})',
                formula,
            )
            formula = re.sub(
                rf'\b{re.escape(c)}\b',
                f'({self.construct_formula_from_path([c], variables)})',
                formula,
            )
            formula = f"({formula} {op} {path[i]})"
        return formula


# Example Usage
analyzer = FormulaAnalyzer('eth_bnbpirates')
analyzer.analyze_formula()
