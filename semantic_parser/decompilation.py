import logging
from global_params import *
import os
from web3 import Web3
import pandas as pd

log = logging.getLogger(__name__)


class Decompiler:
    def __init__(self, platform, address, block_number):
        self.platform = platform
        self.address = address
        self.func_num = 0
        # for development to skip format
        if address.startswith("0x"):
            self.address = self.format_addr(address)
        self.block_number = block_number
        self.path = "./gigahorse-toolchain/.temp/" + self.address + "/out/"
        self.dasm_path = (
            "./gigahorse-toolchain/.temp/" + self.address + "/contract.dasm"
        )
        self.analyze()

    def analyze(self):
        self.set_url()
        self.download_bytecode()
        if os.path.exists(CONTRACT_PATH + self.address + ".hex"):
            self.analyze_contract()
            self.set_func()

    def format_addr(self, addr):
        if len(addr) != 42:
            return "0x" + "0" * (42 - len(addr)) + addr.replace("0x", "")
        else:
            return addr

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
        elif self.platform == "Polygon":
            self.url = "https://polygon-mainnet.g.alchemy.com/v2/K8Y0dy1NhMZHds7-2B27T6wnHDtk8T3A"
        elif self.platform == "Cronos":
            self.url = (
                "https://cro.getblock.io/6ecf1a9f-da32-44cd-9713-9780f45c9dac/mainnet/"
            )
        elif self.platform == "Avalanche":
            self.url = "https://avalanche-mainnet.infura.io/v3/6807f78a636b46c7a7573af66a2e3391"
        elif self.platform == "Fantom":
            self.url = "https://practical-long-energy.fantom.discover.quiknode.pro/fc97af1ebab40f57ea698b6cf3dd67a2d24cac1a/"
        elif self.platform == "Moonbeam":
            self.url = "https://moonbeam.getblock.io/6bf31e7d-f5b2-4860-8e15-aa9a11f6533d/mainnet/"
        elif self.platform == "Arbitrum":
            self.url = (
                "https://arb.getblock.io/6bf31e7d-f5b2-4860-8e15-aa9a11f6533d/mainnet/"
            )
        elif self.platform == "Tron":
            self.url = "https://trx.getblock.io/6bf31e7d-f5b2-4860-8e15-aa9a11f6533d/mainnet/fullnode/jsonrpc"
        elif self.platform == "Optimism":
            self.url = (
                "https://op.getblock.io/6bf31e7d-f5b2-4860-8e15-aa9a11f6533d/mainnet/"
            )
        elif self.platform == "Moonriver":
            self.url = "https://moonriver.getblock.io/6bf31e7d-f5b2-4860-8e15-aa9a11f6533d/mainnet/"
        elif self.platform == "SKALE":
            self.url = (
                "https://staging-v3.skalenodes.com/v1/staging-fast-active-bellatrix"
            )
        elif self.platform == "Base":
            self.url = "https://base-mainnet.public.blastapi.io"
        else:
            self.url = ""
        if self.url.startswith("https"):
            w3 = Web3(Web3.HTTPProvider(self.url))
        else:
            w3 = Web3(Web3.WebsocketProvider(self.url))
        self.block_number = w3.eth.get_block_number()

    def download_bytecode(self):
        log.info("Get contract bytecode...")
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
        logging.info("Decompiling contract...")
        command = (
            "cd ./gigahorse-toolchain && ./gigahorse.py -C ./clients/hyperion.dl "
            + CONTRACT_DIR
            + "{contract_addr}.hex >/dev/null 2>&1"
        )
        os.system(command.format(contract_addr=self.address))

    def set_func(self):
        loc = "./gigahorse-toolchain/.temp/" + self.address + "/out/PublicFunction.csv"
        func_map = {}
        if os.path.exists(loc) and (os.path.getsize(loc) > 0):
            df = pd.read_csv(loc, header=None, sep="	")
            df.columns = ["func", "funcSign"]
            for _, row in df.iterrows():
                func_map[row["funcSign"]] = row["func"]
        self.func_map = func_map
        self.func_num = len(func_map.keys())

    # =======followings are the decompilation information extraction=======
    # receiver of transfer calls
    def get_recipient(self):
        loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_Recipient.csv"
        )
        if os.path.exists(loc) and (os.path.getsize(loc) > 0):
            df = pd.read_csv(loc, header=None, sep="	")
            df.columns = ["callStmt", "to", "funcSign"]
        else:
            df = pd.DataFrame()
        return df

    # get the constrained call by require-msg.sender like pattern
    # val => slot of owner/compared storage var
    def get_call_guarded_info(self):
        loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_CallGuardedByOwner.csv"
        )
        if os.path.exists(loc) and (os.path.getsize(loc) > 0):
            df = pd.read_csv(loc, header=None, sep="	")
            df.columns = ["callStmt", "val", "funcSign"]
        else:
            df = pd.DataFrame()
        return df

    def get_sensitive_call(self):
        loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_SensitiveCall.csv"
        )
        # mark the receiver and the tranfer amount of ETH/ERC token
        if os.path.exists(loc) and (os.path.getsize(loc) > 0):
            df = pd.read_csv(loc, header=None, sep="	")
            df.columns = ["callStmt", "recipient", "amount", "funcSign"]
        else:
            df = pd.DataFrame()
        return df

    def infer_balance(self):
        balance_loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_BalanceSlot.csv"
        )
        if os.path.exists(balance_loc) and (os.path.getsize(balance_loc) > 0):
            df_balance = pd.read_csv(balance_loc, header=None, sep="	")
            df_balance.columns = ["id", "funcSign"]
        else:
            df_balance = pd.DataFrame()
        return df_balance

    def infer_time(self):
        time_loc = (
            "./gigahorse-toolchain/.temp/" + self.address + "/out/Hyperion_TimeSlot.csv"
        )
        if os.path.exists(time_loc) and (os.path.getsize(time_loc) > 0):
            df_time = pd.read_csv(time_loc, header=None, sep="	")
            df_time.columns = ["id", "funcSign"]
        else:
            df_time = pd.DataFrame()
        return df_time

    def infer_supply(self):
        supply_loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_SupplySlot.csv"
        )
        # if has supply (from totalSupply())
        # just use this slot
        if os.path.exists(supply_loc) and (os.path.getsize(supply_loc) > 0):
            df_supply = pd.read_csv(supply_loc, header=None, sep="	")
            df_supply.columns = ["id", "funcSign"]
        else:
            df_supply = pd.DataFrame()
        return df_supply

    def get_supply_amount(self):
        # maybe multiple supply?
        supply_amount = []
        supply_loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_SupplyAmountSlot.csv"
        )
        if os.path.exists(supply_loc) and (os.path.getsize(supply_loc) > 0):
            df_supply = pd.read_csv(supply_loc, header=None, sep="	")
            df_supply.columns = ["id"]
        else:
            df_supply = pd.DataFrame()

        for _, row in df_supply.iterrows():
            supply_amount.append(self.get_storage_num_content(int(row["id"], 16)))
        return supply_amount

    def infer_owner(self):
        owner_loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_OwnerSlot.csv"
        )
        if os.path.exists(owner_loc) and (os.path.getsize(owner_loc) > 0):
            df_owner = pd.read_csv(owner_loc, header=None, sep="	")
            df_owner.columns = ["id"]
        else:
            df_owner = pd.DataFrame()
        return df_owner

    def infer_pause(self):
        loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_PauseSlot.csv"
        )
        if os.path.exists(loc) and (os.path.getsize(loc) > 0):
            df = pd.read_csv(loc, header=None, sep="	")
            df.columns = ["id", "funcSign"]
        else:
            df = pd.DataFrame()
        return df

    def infer_tokenURI(self):
        loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_TokenURIStorage.csv"
        )
        if os.path.exists(loc) and (os.path.getsize(loc) > 0):
            df = pd.read_csv(loc, header=None, sep="	")
            df.columns = ["id", "funcSign"]
        else:
            df = pd.DataFrame()
        return df

    def get_storage_way(self):
        if self.url.startswith("https"):
            w3 = Web3(Web3.HTTPProvider(self.url))
        else:
            w3 = Web3(Web3.WebsocketProvider(self.url))
        # judge 2 conditions
        # 1. tokenuri = string
        # 2. tokenuri[id] = string
        df = self.infer_tokenURI()
        if df.empty:
            return ""
        # maybe multiple uri prefix
        # check for every of them
        token_uri_prefix = []
        for _, row in df.iterrows():
            uri = self.get_storage_string_content(int(row["id"], 16))
            log.info(uri)
            # http and ipfs
            if not ("http" in uri or "ipfs" in uri):
                # use web3 client and abi
                contract_abi = [
                    {
                        "constant": True,
                        "inputs": [{"name": "tokenId", "type": "uint256"}],
                        "name": "tokenURI",
                        "outputs": [{"name": "", "type": "string"}],
                        "payable": False,
                        "stateMutability": "view",
                        "type": "function",
                    }
                ]

                # 创建合约实例
                contract = w3.eth.contract(
                    address=Web3.to_checksum_address(self.address), abi=contract_abi
                )
                # 调用tokenURI函数
                # sometimes 0 is not valid for a tokenid
                token_id = 1
                try:
                    uri = contract.functions.tokenURI(token_id).call()
                except Exception as e:
                    log.error(e)
                    uri = ""
                log.info(uri)
            # just use the protocal
            if uri not in token_uri_prefix:
                token_uri_prefix.append(uri)
                if "http" in uri:
                    self.http_storage = True
                    return "http"
                elif "ipfs" in uri:
                    self.ipfs_storage = True
                    return "ipfs"
                elif "base64" in uri:
                    self.base64 = True
                    return "base64"

    def get_storage_num_content(self, slot_index):
        if self.url.startswith("https"):
            w3 = Web3(Web3.HTTPProvider(self.url))
        else:
            w3 = Web3(Web3.WebsocketProvider(self.url))
        contract_address = Web3.to_checksum_address(self.address)
        storage_content = w3.eth.get_storage_at(contract_address, slot_index)
        log.info(str(storage_content.hex()))
        return int(storage_content.hex(), 16)

    def get_storage_string_content(self, slot_index):
        if self.url.startswith("https"):
            w3 = Web3(Web3.HTTPProvider(self.url))
        else:
            w3 = Web3(Web3.WebsocketProvider(self.url))
        contract_address = Web3.to_checksum_address(self.address)
        storage_content = w3.eth.get_storage_at(contract_address, slot_index)
        try:
            string_content = storage_content.decode("utf-8").replace("\x00", "")
        except:
            string_content = ""
        return string_content

    def get_storage_content(self, slot_index, byteLow, byteHigh):
        if self.url.startswith("https"):
            w3 = Web3(Web3.HTTPProvider(self.url))
        else:
            w3 = Web3(Web3.WebsocketProvider(self.url))
        contract_address = Web3.to_checksum_address(self.address)
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

    def get_slot_tainted_by_owner(self):
        loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_SlotTaintedByOwner.csv"
        )
        if os.path.exists(loc) and (os.path.getsize(loc) > 0):
            df = pd.read_csv(loc, header=None, sep="	")
            df.columns = ["slot", "owner", "funcSign"]
        else:
            df = pd.DataFrame()
        return df

    def get_guarded_mint(self):
        loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_GuardedMint.csv"
        )
        if os.path.exists(loc) and (os.path.getsize(loc) > 0):
            df = pd.read_csv(loc, header=None, sep="	")
            df.columns = ["slot", "funcSign"]
        else:
            df = pd.DataFrame()
        return df

    def get_clear_call(self):
        loc = (
            "./gigahorse-toolchain/.temp/"
            + self.address
            + "/out/Hyperion_ClearBalance.csv"
        )
        if os.path.exists(loc) and (os.path.getsize(loc) > 0):
            df = pd.read_csv(loc, header=None, sep="	")
            df.columns = ["callStmt", "funcSign"]
        else:
            df = pd.DataFrame()
        return df
