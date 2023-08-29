from web3 import Web3
import csv

# Connect to Ethereum node
w3 = Web3(
    Web3.WebsocketProvider(
        'wss://bsc.getblock.io/6bf31e7d-f5b2-4860-8e15-aa9a11f6533d/mainnet/'
    )
)
address = "0x5a04565ee1c90c84061ad357ae9e2f1c32d57dc6"
addr = w3.to_checksum_address(address)
bytecode = w3.eth.get_code(addr).hex()

print(bytecode)
