import regex as re
from web3 import Web3
import logging

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
        else:
            self.url = ""

    def extract_coefficient_from_division(self, expr):
        # match outer bvudiv_i function
        pattern = r"bvudiv_i\s*\(\s*((?:[^,()]+|(?R))+)\s*,\s*((?:[^,()]+|(?R))+)\)"
        match = re.search(pattern, expr)

        if not match:
            return None, None

        numerator_expr = match.group(1).strip()
        denominator_expr = match.group(2).strip()

        log.info(numerator_expr)
        log.info(denominator_expr)

        return numerator_expr, denominator_expr

    def get_chain_value(self, store_slot):
        if self.url.startswith("https"):
            w3 = Web3(Web3.HTTPProvider(self.url))
        else:
            w3 = Web3(Web3.WebsocketProvider(self.url))
        contract_address = Web3.to_checksum_address(self.address)
        # judge storage value
        if "Ia_store" in store_slot:
            slot_number = int(store_slot.split('-')[1])
            storage_value = w3.eth.get_storage_at(contract_address, slot_number)
            return int(storage_value.hex(), 16)
        # return if is const
        try:
            return int(expr)
        except:
            pass
        # for other expr
        return None

    def compute_coefficient(self, expr):
        numerator_expr, denominator_expr = self.extract_coefficient_from_division(expr)
        if not numerator_expr:
            return None

        # extract coefficient
        coeff_match = re.search(r'^\d+', numerator_expr)
        if coeff_match:
            numerator_expr = coeff_match.group(0)

        numerator_value = self.get_chain_value(numerator_expr)
        if denominator_expr.isdigit():
            denominator_value = int(denominator_expr)
        else:
            denominator_value = self.get_chain_value(denominator_expr)

        # divide 0 case handler
        if denominator_value == 0:
            return float('inf')
        log.info(numerator_value)
        log.info(denominator_value)
        coefficient = numerator_value / denominator_value
        log.info(coefficient)
        return coefficient


# test case remained
contract_address = "0xf7DE7E8A6bd59ED41a4b5fe50278b3B7f31384dF"
expr = "bvudiv_i(Ia_store-14-*\n         bvudiv_i(1000000000000000000*Id_4*mem_mem_64,\n                  1000000000000000000),\n         10000)"
