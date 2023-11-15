from web3 import Web3
import logging
from z3 import *

from symbolic_execution.utils import *

log = logging.getLogger(__name__)


class StateExtractor:
    def __init__(self, platform, address, block_number):
        self.platform = platform
        self.address = address
        # for development to skip format
        if address.startswith("0x"):
            self.address = self.format_addr(address)
        self.block_number = block_number
        self.set_url()

    def format_addr(self, addr):
        if len(addr) != 42:
            return "0x" + "0" * (42 - len(addr)) + addr.replace("0x", "")
        else:
            return addr

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

    # used by the checker in a pragram point
    # get the states of the point
    def get_from_var(self, expr):
        if not is_expr(expr):
            return
        list_vars = get_vars(expr)
        for var in list_vars:
            # check if a var is global
            if is_storage_var(var):
                pos = get_storage_position(var)
                constant = self.get_chain_value(pos)
                log.info({pos: constant})

    def get_chain_value(self, var):
        if self.url.startswith("https"):
            w3 = Web3(Web3.HTTPProvider(self.url))
        else:
            w3 = Web3(Web3.WebsocketProvider(self.url))
        contract_address = Web3.to_checksum_address(self.address)
        # judge storage value
        if is_storage_var(var):
            slot_number = get_storage_position(var)
            storage_value = w3.eth.get_storage_at(contract_address, slot_number)
            return int(storage_value.hex(), 16)
        return None
