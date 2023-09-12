from web3 import Web3
import csv

# Connect to Ethereum node
w3 = Web3(
    Web3.WebsocketProvider(
        'wss://bsc.getblock.io/6bf31e7d-f5b2-4860-8e15-aa9a11f6533d/mainnet/'
    )
)
address = "0x8a0c542ba7bbbab7cf3551ffcc546cdc5362d2a1"
addr = w3.to_checksum_address(address)
bytecode = w3.eth.get_code(addr).hex()

print(bytecode)

# storage_content = w3.eth.get_storage_at(addr, 1)
# print(storage_content.decode('utf-8').replace('\x00', ''))
