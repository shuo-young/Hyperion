import os
from global_params import *
import pandas as pd
from web3 import Web3


class Semantics:
    def __init__(self, platform, address, block_number):
        self.platform = platform
        self.address = address
        # for development to skip format
        if address.startswith("0x"):
            self.address = self.format_addr(address)
        self.block_number = block_number
        self.analyze()
        self.targeted_funcs = []
        self.transfer_funcs = []

    def format_addr(self, addr):
        if len(addr) != 42:
            return "0x" + "0" * (42 - len(addr)) + addr.replace("0x", "")
        else:
            return addr

    def analyze(self):
        self.set_url()
        self.download_bytecode()
        if os.path.exists(CONTRACT_PATH + self.address + ".hex"):
            self.analyze_contract()
            # Critical semantics extraction
            self.analyze_formula()  # transfer amount formula recovery
            # deprecated
            # self.analyze_lock_time()
            # self.analyze_unlimited_mint()
            # self.analyze_clear_ETH()

    # extendable for more platforms
    def set_url(self):
        if self.platform == "ETH":
            self.url = (
                "https://eth-mainnet.g.alchemy.com/v2/6t0LpEw9cr0OlGIVTFqs92aOIkfhktMk"
            )
        elif self.platform == "BSC":
            self.url = (
                "wss://bsc.getblock.io/6bf31e7d-f5b2-4860-8e15-aa9a11f6533d/mainnet/"
            )
        else:
            self.url = ""

    def download_bytecode(self):
        if self.url == "":
            return
        loc = CONTRACT_PATH + self.address + ".hex"
        if os.path.exists(loc):
            return
        else:
            if self.url.startswith("https"):
                w3 = Web3(Web3.HTTPProvider(self.url))
            else:
                w3 = Web3(Web3.WebsocketProvider(self.url))
            contract_address = Web3.to_checksum_address(self.address)
            code = str(w3.eth.get_code(contract_address).hex())
            if code != "0x":
                with open(loc, "w") as f:
                    f.write(code[2:])

    def analyze_contract(self):
        # use hyperion client to analyze the contract
        command = (
            "cd ./gigahorse-toolchain && ./gigahorse.py -j 20 -C ./clients/hyperion.dl "
            + CONTRACT_DIR
            + "{contract_addr}.hex >/dev/null 2>&1"
        )
        os.system(command.format(contract_addr=self.address))

    # receiver of transfer calls
    def get_recipient(self):
        loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_Recipient.csv"
        )
        if os.path.exists(loc) and (os.path.getsize(loc) > 0):
            df = pd.read_csv(loc, header=None, sep='	')
            df.columns = ["callStmt", "to", "funcSign"]
        else:
            df = pd.DataFrame()
        return df

    # get the constrained call by require-msg.sender like pattern
    # val => slot of owner/compared storage var
    def get_call_constrain_info(self):
        loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_CallConstrainedByOwner.csv"
        )
        if os.path.exists(loc) and (os.path.getsize(loc) > 0):
            df = pd.read_csv(loc, header=None, sep='	')
            df.columns = ["callStmt", "val", "funcSign"]
        else:
            df = pd.DataFrame()
        return df

    # deprecated for just dataflow backward analysis
    def analyze_formula(self):
        loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_SensitiveCall.csv"
        )
        # mark the receiver and the tranfer amount of ETH/ERC token
        if os.path.exists(loc) and (os.path.getsize(loc) > 0):
            df = pd.read_csv(loc, header=None, sep='	')
            df.columns = ["callStmt", "recipient", "amount"]
        else:
            df = pd.DataFrame()
        # print(df)
        if df.empty:
            return

        return_private_bridge_loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_PrivateCallReturn.csv"
        )

        private_callarg_bridge_loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_CallPrivateFuncArg.csv"
        )

        # from etheAmount to its origin (reverse)
        # add
        add_loc = (
            "./gigahorse-toolchain/.temp/" + self.address + "/out/Hyperion_Add.csv"
        )
        # add_df = self.extract_math(add_loc)

        # sub
        sub_loc = (
            "./gigahorse-toolchain/.temp/" + self.address + "/out/Hyperion_Sub.csv"
        )
        # sub_df = self.extract_math(sub_loc)

        # mul
        mul_loc = (
            "./gigahorse-toolchain/.temp/" + self.address + "/out/Hyperion_Mul.csv"
        )
        # mul_df = self.extract_math(mul_loc)

        # div
        div_loc = (
            "./gigahorse-toolchain/.temp/" + self.address + "/out/Hyperion_Div.csv"
        )
        # div_df = self.extract_math(div_loc)

        variables = {}
        return_private_to_call_private_return = {}
        return_private_bridge = pd.read_csv(
            return_private_bridge_loc, header=None, sep='	'
        )
        private_callarg_bridge = pd.read_csv(
            private_callarg_bridge_loc, header=None, sep='	'
        )
        call_private_stmt_def_dict = {}
        for index, row in return_private_bridge.iterrows():
            if str(row[1]) not in return_private_to_call_private_return.keys():
                return_private_to_call_private_return[str(row[1])] = [str(row[2])]
            else:
                return_private_to_call_private_return[str(row[1])].append(str(row[2]))
            call_private_stmt_def_dict[str(row[2])] = str(row[0])

        # read op csv
        self.process_csv(
            variables, return_private_to_call_private_return, add_loc, 'ADD'
        )
        self.process_csv(
            variables, return_private_to_call_private_return, sub_loc, 'SUB'
        )
        self.process_csv(
            variables, return_private_to_call_private_return, mul_loc, 'MUL'
        )
        self.process_csv(
            variables, return_private_to_call_private_return, div_loc, 'DIV'
        )
        # print(variables)
        # sink site: transfer amount
        sink_site_variable = df["amount"].unique()
        # print(sink_site_variable)
        for var in sink_site_variable:
            final_formula = self.expand_expression(variables, var)
            print(f"The final formula for {var} is {final_formula}")

        # we now know the transfer target and amount
        # use the recipient role to find clearETH pattern risky withdrawl
        # 1.transfer 2.caller 3.caller constrained by slot load
        recipient = self.get_recipient()
        call_contrain = self.get_call_constrain_info()
        merged_df = df.merge(recipient, on='callStmt').merge(
            call_contrain, on='callStmt'
        )
        if len(merged_df) > 0:
            print("true clear ETH!")
        return

    def process_csv(
        self, variables, return_private_to_call_private_return, file_path, operation
    ):
        df = pd.read_csv(file_path, header=None, sep='	')
        for index, row in df.iterrows():
            a, b, c = str(row[0]), str(row[1]), str(row[2])
            if c in return_private_to_call_private_return.keys():
                c_ = return_private_to_call_private_return[c]
                for c in c_:
                    if operation == 'ADD':
                        variables[c] = (a, b, '+')
                    elif operation == 'SUB':
                        variables[c] = (a, b, '-')
                    elif operation == 'DIV':
                        variables[c] = (a, b, '/')
                    elif operation == 'MUL':
                        variables[c] = (a, b, '*')

            else:
                if operation == 'ADD':
                    variables[c] = (a, b, '+')
                elif operation == 'SUB':
                    variables[c] = (a, b, '-')
                elif operation == 'DIV':
                    variables[c] = (a, b, '/')
                elif operation == 'MUL':
                    variables[c] = (a, b, '*')

    def expand_expression(self, variables, var):
        if var not in variables:
            return var
        a, b, op = variables[var]
        return f'({self.expand_expression(variables,a)}) {op} ({self.expand_expression(variables,b)})'

    def analyze_lock_time(self):
        lock_loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_LockLiquidity.csv"
        )
        if os.path.exists(lock_loc) and (os.path.getsize(lock_loc) > 0):
            df_lock = pd.read_csv(lock_loc, header=None, sep='	')
            df_lock.columns = ["funcSign", "slotNum"]
        else:
            df_lock = pd.DataFrame()

        if df_lock.empty:
            return
        unlock_loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_UnlockLiquidity.csv"
        )

        if os.path.exists(unlock_loc) and (os.path.getsize(unlock_loc) > 0):
            df_unlock = pd.read_csv(unlock_loc, header=None, sep='	')
            df_unlock.columns = ["funcSign", "slotNum"]
        else:
            df_unlock = pd.DataFrame()

        if df_unlock.empty:
            return

        # merge A and B, finding its same slotNum and different funcSign
        res = pd.merge(df_lock, df_unlock, how='left', on='slotNum')
        # print(res)
        # funcSign_x differ funcSign_y

    def analyze_unlimited_mint(self):
        om_loc = (
            "./gigahorse-toolchain/.temp/" + self.address + "/out/Hyperion_OverMint.csv"
        )
        if os.path.exists(om_loc) and (os.path.getsize(om_loc) > 0):
            df_om = pd.read_csv(om_loc, header=None, sep='	')
            df_om.columns = ["funcSign", "supplySlotNum", "ownerSlot", "id"]
        else:
            df_om = pd.DataFrame()

        if df_om.empty:
            return

        print(len(df_om))

    def analyze_clear_ETH(self):
        ce_loc = (
            "./gigahorse-toolchain/.temp/" + self.address + "/out/Hyperion_ClearETH.csv"
        )
        if os.path.exists(ce_loc) and (os.path.getsize(ce_loc) > 0):
            df_ce = pd.read_csv(ce_loc, header=None, sep='	')
            df_ce.columns = ["funcSign", "ownerSlot", "ethAmount"]
        else:
            df_ce = pd.DataFrame()

        if df_ce.empty:
            return

        print(len(df_ce))

    def infer_balance(self):
        balance_loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_BalanceSlot.csv"
        )
        if os.path.exists(balance_loc) and (os.path.getsize(balance_loc) > 0):
            df_balance = pd.read_csv(balance_loc, header=None, sep='	')
            df_balance.columns = ["id"]
        else:
            df_balance = pd.DataFrame()
        return df_balance

    def infer_time(self):
        time_loc = (
            "./gigahorse-toolchain/.temp/" + self.address + "/out/Hyperion_TimeSlot.csv"
        )
        if os.path.exists(time_loc) and (os.path.getsize(time_loc) > 0):
            df_time = pd.read_csv(time_loc, header=None, sep='	')
            df_time.columns = ["id"]
        else:
            df_time = pd.DataFrame()
        return df_time

    def infer_supply(self):
        supply_loc = (
            "./gigahorse-toolchain/.temp/" + self.address + "/out/Hyperion_TimeSlot.csv"
        )
        if os.path.exists(supply_loc) and (os.path.getsize(supply_loc) > 0):
            df_supply = pd.read_csv(supply_loc, header=None, sep='	')
            df_supply.columns = ["id"]
        else:
            df_supply = pd.DataFrame()
        return df_supply

    def infer_owner(self):
        owner_loc = (
            "./gigahorse-toolchain/.temp/" + self.address + "/out/Hyperion_TimeSlot.csv"
        )
        if os.path.exists(owner_loc) and (os.path.getsize(owner_loc) > 0):
            df_owner = pd.read_csv(owner_loc, header=None, sep='	')
            df_owner.columns = ["id"]
        else:
            df_owner = pd.DataFrame()
        return df_owner

    def get_storage_content(self, slot_index, byteLow, byteHigh):
        if self.url.startswith("https"):
            w3 = Web3(Web3.HTTPProvider(self.url))
        else:
            w3 = Web3(Web3.WebsocketProvider(self.url))
        contract_address = Web3.to_checksum_address(self.storage_addr)
        storage_content = str(
            w3.eth.get_storage_at(contract_address, slot_index, self.block_number).hex()
        )
        storage_content = storage_content.replace("0x", "")
        # get storage address
        if byteLow == 0:
            contract_addr = "0x" + storage_content[-(byteHigh + 1) * 2 :]
        else:
            contract_addr = "0x" + storage_content[-(byteHigh + 1) * 2 : -byteLow * 2]
        # maybe other type of storage, like string etc
        return contract_addr
