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

    def compute_fee_rate(self, expr):
        if not is_expr(expr):
            log.info("not experssion")
            return None
        if not expr.decl().kind() == Z3_OP_BUDIV_I:
            log.info("not div")
            if expr.decl().kind() == Z3_OP_CONCAT:
                log.info("is concat")
                second_element = expr.arg(1)
                log.info(second_element)
                if second_element.decl().kind() == Z3_OP_EXTRACT:
                    try:
                        expr = second_element.arg(0)
                        log.info(expr)
                    except:
                        pass
            else:
                return None
        # sample: bvudiv_i(5 * Iv, 100)
        factor = self.obtain_factor_value(expr.arg(0))
        denominator = self.obtain_denominator_value(expr.arg(1))  # 100
        log.info(factor)
        log.info(denominator)
        if factor and denominator:
            fee_rate = float(factor / denominator)  # 5/100
            return fee_rate
        return None

    def obtain_factor_value(self, expr):
        if not is_expr(expr):
            return None
        if not expr.decl().kind() == Z3_OP_BMUL:
            return None
        factor = expr.arg(0)  # 5
        log.info("factor")
        log.info(factor)
        var = expr.arg(1)
        log.info(var)
        # loose constraint
        # if not self.is_msgvalue_or_datavar(var):
        #     return None
        if is_bv_value(factor):
            return factor.as_long()
        elif is_storage_var(factor):
            try:
                return self.get_chain_value(factor)
            except:
                return None
        return None

    def obtain_denominator_value(self, var):
        if is_bv_value(var):
            return var.as_long()
        elif is_storage_var(var):
            try:
                return self.get_chain_value(var)
            except:
                return None
        return None

    def is_msgvalue_or_datavar(self, var):
        if not is_expr(var):
            return False
        if not isinstance(var, str):
            var = var.decl().name()
        return var == "Iv" or var.startswith("Id_")
