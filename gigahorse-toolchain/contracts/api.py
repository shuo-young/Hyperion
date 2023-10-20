from web3 import Web3

# Connect to Ethereum node
# PLY: wss://polygon-mainnet.g.alchemy.com/v2/K8Y0dy1NhMZHds7-2B27T6wnHDtk8T3A
# w3 = Web3(
#     Web3.HTTPProvider(
#         'https://eth-mainnet.g.alchemy.com/v2/6t0LpEw9cr0OlGIVTFqs92aOIkfhktMk'
#     )
# )

w3 = Web3(
    Web3.WebsocketProvider(
        'wss://bsc.getblock.io/6bf31e7d-f5b2-4860-8e15-aa9a11f6533d/mainnet/'
    )
)


def get_bytecode(address):
    addr = w3.to_checksum_address(address)
    bytecode = w3.eth.get_code(addr).hex()
    print(bytecode)
    return bytecode


def get_storage(address, slot):
    addr = w3.to_checksum_address(address)
    storage_content = w3.eth.get_storage_at(addr, slot)
    print(storage_content)


address = "0x9A78649501BbAAC285Ea4187299471B7ad4ABD35"
bytecode = get_bytecode(address)
