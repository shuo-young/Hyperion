from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
import os


script_dir = os.path.dirname(os.path.abspath(__file__))

dapp_list_dir = os.path.join(script_dir, "folder_name")

# Create 'dapp list' directory if it doesn't exist
if not os.path.exists(dapp_list_dir):
    os.makedirs(dapp_list_dir)

chrome_option = webdriver.ChromeOptions()
p = r"C:\path\to\your\chrome\user\data"
chrome_option.add_argument("--user-data-dir=" + p)
chrome_option.add_argument("--disable-blink-features=AutomationControlled")
chrome_option.add_experimental_option(
    "excludeSwitches", ["enable-automation", "enable-logging"]
)
browser = webdriver.Chrome(options=chrome_option)


for page in range(1, 61):
    url = "https://dappradar.com/rankings/games/chain/ethereum/9?range=30d&sort=totalVolumeInFiat&order=desc&resultsPerPage=50"
    browser.get(url)
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "dapp-name-link-comp"))
    )

    for i in browser.find_elements(by=By.CLASS_NAME, value="dapp-name-link-comp"):
        name = i.get_attribute("title").replace(":", "")  # Remove colon from the name
        # Define the path for the current dapp's directory within 'dapp list'
        dapp_dir = os.path.join(dapp_list_dir, name)
        if not os.path.exists(dapp_dir):
            os.makedirs(dapp_dir)

        browser.execute_script(
            'window.open("{}")'.format(
                i.get_attribute("href")
                + "/smart-contracts?resultsPerPage-sc=50&page-sc=1"
            )
        )
        browser.switch_to.window(browser.window_handles[-1])

        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "sc-dkrFOg.kNAZIw"))
        )

        with open(os.path.join(dapp_dir, "contract.txt"), "w") as f:
            for j in browser.find_elements(by=By.CLASS_NAME, value="sc-dkrFOg.kNAZIw"):
                f.write(f"{j.text}\n")

        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.sc-dkrFOg.crVJDe"))
        )
        link_element = browser.find_element(
            by=By.CSS_SELECTOR, value="a.sc-dkrFOg.crVJDe"
        )
        with open(os.path.join(dapp_dir, "link.txt"), "w") as link_file:
            link_file.write(link_element.get_attribute("href") + "\n")

        browser.close()
        browser.switch_to.window(browser.window_handles[0])

browser.quit()
