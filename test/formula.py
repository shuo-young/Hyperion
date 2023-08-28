import pandas as pd
import os


class FormulaAnalyzer:
    def __init__(self, address):
        self.address = address

    def analyze_formula(self):
        # Load the data from CSV files
        relations = ['Add', 'Sub', 'Mul', 'Div']
        base_path = f"./gigahorse-toolchain/.temp/{self.address}/out/"
        relation_dfs = {
            rel: pd.read_csv(
                f"{base_path}" + "Hyperion_{rel}.csv", header=None, sep='\t'
            )
            for rel in relations
        }
        sink_loc = base_path + "Hyperion_SensitiveCall.csv"
        call_df = pd.read_csv(sink_loc, header=None, sep='\t')
        call_df.columns = ["funcSign", "ethAmount", "ethAmountFrom", "all"]

        # Construct a dictionary to store the relationship of variables
        var_relationships = {}
        for rel, df in relation_dfs.items():
            self.populate_var_relationships(df, var_relationships, rel)

        # Process the call data and analyze the formulas
        for _, row in call_df.iterrows():
            recipient = row['recipient']
            amount = row['amount']
            amount_from = row['amountFrom']
            formula = self.find_formula(var_relationships, amount_from, amount)
            print(f"The formula to get {amount} from {amount_from} is: {formula}")

    def populate_var_relationships(self, df, relationships, relation_type):
        for _, row in df.iterrows():
            a, b, c = str(row['a']), str(row['b']), str(row['res'])
            if c not in relationships:
                relationships[c] = []
            relationships[c].append((relation_type, a, b))

    def find_formula(self, var_relationships, source_var, target_var):
        if source_var == target_var:
            return source_var

        if target_var not in var_relationships:
            return None

        for relation_type, a, b in var_relationships[target_var]:
            formula_a = self.find_formula(var_relationships, source_var, a)
            formula_b = self.find_formula(var_relationships, source_var, b)
            if formula_a and formula_b:
                return f"({formula_a} {relation_type} {formula_b})"

        return None


# Example Usage
analyzer = FormulaAnalyzer('eth_bnbpirates')
analyzer.analyze_formula()
