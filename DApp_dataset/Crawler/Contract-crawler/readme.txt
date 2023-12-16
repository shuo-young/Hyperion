This script is designed for scraping and saving the smart contract code of the Dapp contract address that were previous saved by Dappradar-crawler. It accesses multiple blockchain explorer APIs (such as Etherscan, BscScan, etc.) to obtain the source code of specified smart contracts. Here are the steps for using this script:

### Usage Steps

1. **Environment Setup**:
   - Ensure Python is installed on your system.
   - Install the `requests` library, if not already installed, by running `pip install requests`.

2. **Setting up API Keys**:
   - The script includes API URLs for various blockchain explorers, but you need to provide your own API keys. You can obtain these keys by registering on the respective blockchain explorer websites.
   - Insert your acquired API keys into the respective URLs in the script. For example:
     ```python
     ('Etherscan', f'https://api.etherscan.io/api?module=contract&action=getsourcecode&address={contract_address}&apikey=YourAPIKey')
     ```

3. **Configuring Directories**:
   - Set the `base_directory` variable in the `process_contracts` function to the path of your base directory where Dapp smart contract addresses are stored. For example:
     ```python
     base_directory = 'path\to\your\directory'
     ```
   - If you have additional directories to process, add their paths to the `additional_directories` list.

4. **Running the Script**:
   - Run this Python script. It will iterate through each subdirectory in the specified base directory, read the `contract.txt` file, obtain the smart contract addresses, and attempt to fetch the source code from the APIs listed.
   - If the source code is found, the script will save it in a `.sol` file named after the contract address.

### Important Notes
- Ensure you have the right to access the APIs and comply with the terms of use of the respective APIs.
- A stable internet connection is required as the script accesses external APIs.
- If there are changes in the structure or parameters of the blockchain explorer APIs, the script may need corresponding modifications.

This script facilitates the automated retrieval of smart contract source code from multiple blockchain explorers, which is highly beneficial for blockchain development and research.
