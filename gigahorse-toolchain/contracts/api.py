from web3 import Web3
import csv

# Connect to Ethereum node
w3 = Web3(
    Web3.WebsocketProvider(
        'wss://bsc.getblock.io/6bf31e7d-f5b2-4860-8e15-aa9a11f6533d/mainnet/'
    )
)
address = "0x5Cf8eA4278f689B301C4a17DdCa9D5ec8b0B0511"
addr = w3.to_checksum_address(address)
bytecode = w3.eth.get_code(addr).hex()

print(bytecode)
