This script is a Python script using the Selenium library for browser automation. It's designed to scrape information about Ethereum blockchain-based dapps (decentralized applications) from the DappRadar website, including their names, website links, and smart contract addresses. Here are the steps to use this script:

### Installation Requirements
1. **Python**: Ensure Python is installed on your system.
2. **Selenium Library**: Install Selenium by running `pip install selenium`.
3. **ChromeDriver**: Install ChromeDriver that matches the version of your Chrome browser, and ensure it's in your system path.

### Setting Up the Script
1. **User Data Path**: Modify the `p` variable in the script to point to your Chrome user data directory. This allows Selenium to use your existing Chrome profile, like logged-in sessions, cookies, etc.

   Example:
   ```python
   p = r'C:\path\to\your\chrome\user\data'
   ```

2. **Setting the Dapp List URL**: Modify the `url` variable in the script to point to the DappRadar dapp listing page. For example, to scrape Ethereum blockchain-based game dapps, you would use the following URL:
   ```python
   url = 'https://dappradar.com/rankings/games/chain/ethereum/9?range=30d&sort=totalVolumeInFiat&order=desc&resultsPerPage=50'
   ```

   You can modify this URL to focus on different categories or blockchain platforms depending on your needs.

3. **Download Directory**: The script will create a folder named `folder_name` in its directory to store the scraped data. Ensure the script has necessary permissions to create and write files in this path.

### Running the Script
Once set up, run the script to start the scraping process. The script will automatically open the Chrome browser and navigate to the DappRadar website to gather information about the dapps.

### Workflow of the Script
1. Opens the DappRadar website and locates the list of Ethereum-based dapps.
2. Iterates through each dapp, capturing its name, website link, and smart contract address.
3. Saves this information in text files within folders named after each dapp. (The contract address of Dapp is saved as 'contract.txt' and website link is saved as 'link.txt')