import os
import requests as rq

# Headers for the request
send_headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def download_contract_source(root, folder_name, contract_address, retries=3):
    apis = [
        (
            "Etherscan",
            f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={contract_address}&apikey=HPB1MEZ5YEJ7GZJF7ASQDJ4MPU7YEUTIUT",
        ),
        (
            "BscScan",
            f"https://api.bscscan.com/api?module=contract&action=getsourcecode&address={contract_address}&apikey=9ZQJN9E9Y8F1E7W4TXW4N7VPQBX7ZKA7CP",
        ),
        (
            "PolygonScan",
            f"https://api.polygonscan.com/api?module=contract&action=getsourcecode&address={contract_address}&apikey=MXYBJ5SPK9P2GEWPT2ZCUT1XXQUEPIVWD8",
        ),
        (
            "Cronoscan",
            f"https://api.cronoscan.com/api?module=contract&action=getsourcecode&address={contract_address}&apikey=FD9TPSBQUVJHSVA3F4EKMKNMB3NXSWMXJF",
        ),
        (
            "Snowtrace",
            f"https://api.snowtrace.io/api?module=contract&action=getsourcecode&address={contract_address}&apikey=XAK4BE6TQG85NCS1X26616XNK8C8JE11F3",
        ),
        (
            "FtmScan",
            f"https://api.ftmscan.com/api?module=contract&action=getsourcecode&address={contract_address}&apikey=PYCC95BNX3Q4DZPJFSIC5WHP48D1HTMNND",
        ),
        (
            "MoonbeamScan",
            f"https://api-moonbeam.moonscan.io/api?module=contract&action=getsourcecode&address={contract_address}&apikey=UNERV7KXM7F16CPFJD3TBDAA2CH7346BH7",
        ),
        (
            "Arbiscan",
            f"https://api.arbiscan.io/api?module=contract&action=getsourcecode&address={contract_address}&apikey=1EGATMSYU6M4FGKGRCUP344WVNXHCSZMKH",
        ),
        (
            "OptimismScan",
            f"https://api-optimistic.etherscan.io/api?module=contract&action=getsourcecode&address={contract_address}&apikey=AKBZJI7HYRRWYCNAJTG46WRWDUWMM3I1F8",
        ),
        (
            "MoonriverScan",
            f"https://api-moonriver.moonscan.io/api?module=contract&action=getsourcecode&address={contract_address}&apikey=V4TV2T51QV8B3944Z9QBEAFJZC9XAR8WIH",
        ),
    ]

    for api_name, api_url in apis:
        attempt = 0
        while attempt < retries:
            try:
                response = rq.get(api_url, headers=send_headers)

                if response.status_code == 200:
                    result = response.json()["result"][0]
                    if "SourceCode" in result and result["SourceCode"]:
                        code = result["SourceCode"]
                        file_path = os.path.join(root, f"{contract_address}.sol")
                        if not os.path.exists(file_path):
                            with open(file_path, "w", encoding="utf-8") as file:
                                file.write(code)
                            print(
                                f"Folder '{folder_name}': Successfully downloaded contract from address {contract_address} ({api_name})"
                            )
                            return True
                        else:
                            print(
                                f"Folder '{folder_name}': Contract file already exists, skipping address {contract_address}"
                            )
                            return True
                break  # If response status code is not 200, break and try next API

            except ConnectionResetError:
                print(
                    f"Folder '{folder_name}': Connection reset error, retry {attempt + 1}/{retries}, Address: {contract_address}"
                )
                attempt += 1  # Increase attempt count if ConnectionResetError occurs
            except Exception as e:
                print(
                    f"Folder '{folder_name}': Error encountered, Address: {contract_address}. Error: {e}"
                )
                break  # Break and try next API on other exceptions

    print(
        f"Folder '{folder_name}': Contract source code not found, skipping address {contract_address}"
    )
    return False


def process_contracts(base_directory):
    # Add paths to other directories you want to process
    # Example: ['path\\to\\directory1', 'path\\to\\directory2']
    additional_directories = []

    # Process the base directory first
    for folder in os.listdir(base_directory):
        folder_path = os.path.join(base_directory, folder)
        if os.path.isdir(folder_path):
            contract_file = os.path.join(folder_path, "contract.txt")
            if os.path.exists(contract_file):
                with open(contract_file, "r") as f:
                    for address in f:
                        download_contract_source(folder_path, folder, address.strip())

    # Process additional directories
    for directory in additional_directories:
        for folder in os.listdir(directory):
            folder_path = os.path.join(directory, folder)
            if os.path.isdir(folder_path):
                contract_file = os.path.join(folder_path, "contract.txt")
                if os.path.exists(contract_file):
                    with open(contract_file, "r") as f:
                        for address in f:
                            download_contract_source(
                                folder_path, folder, address.strip()
                            )


if __name__ == "__main__":
    base_directory = "path\\to\\your\\base\\directory"
    process_contracts(base_directory)
