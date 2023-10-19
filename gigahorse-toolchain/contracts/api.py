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


def get_bycode(address):
    addr = w3.to_checksum_address(address)
    bytecode = w3.eth.get_code(addr).hex()
    print(bytecode)
    return bytecode


address = "0xf7DE7E8A6bd59ED41a4b5fe50278b3B7f31384dF"
addr = w3.to_checksum_address(address)

storage_content = w3.eth.get_storage_at(addr, 14)
print(storage_content)
