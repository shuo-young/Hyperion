import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException


def download_html_and_images_with_selenium(base_path):
    # Custom Chrome configuration
    chrome_option = webdriver.ChromeOptions()
    user_data_path = r"C:\Users\AppData\Local\Google\Chrome\User Data"
    chrome_option.add_argument("--user-data-dir=" + user_data_path)
    chrome_option.add_argument("--disable-blink-features=AutomationControlled")
    chrome_option.add_experimental_option(
        "excludeSwitches", ["enable-automation", "enable-logging"]
    )
    chrome_option.add_argument("--disable-extensions")  # Disable extensions

    # Create a WebDriver instance
    driver = webdriver.Chrome(options=chrome_option)

    for folder in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder)

        if os.path.isdir(folder_path):
            link_file_path = os.path.join(folder_path, "link.txt")
            if os.path.exists(link_file_path):
                with open(link_file_path, "r") as file:
                    url = file.read().strip()
                    try:
                        driver.get(url)
                        final_url = driver.current_url
                        html_content = driver.page_source

                        # Save the HTML file
                        html_file_path = os.path.join(folder_path, "index.html")
                        with open(html_file_path, "w", encoding="utf-8") as html_file:
                            html_file.write(html_content)

                        # Retrieve and save all images
                        images = driver.find_elements(By.TAG_NAME, "img")
                        for i, img in enumerate(images):
                            src = img.get_attribute("src")
                            if src:
                                try:
                                    img_response = requests.get(src)
                                    img_file_path = os.path.join(
                                        folder_path, f"image_{i}.jpg"
                                    )
                                    with open(img_file_path, "wb") as img_file:
                                        img_file.write(img_response.content)
                                except Exception as e:
                                    print(f"Failed to download image. Reason: {e}")

                        print(
                            f"Successfully downloaded website source code and images for folder {folder}, from: {final_url}"
                        )
                    except WebDriverException as e:
                        print(
                            f"Failed to download website source code for folder {folder}. Reason: {e}"
                        )
            else:
                print(f"No link.txt file found in folder {folder}.")
        else:
            print(f"{folder} is not a directory.")

    driver.quit()


# How to use
base_path = "The_path"
# polygon finished

# C:\\Users\\huang\Desktop\\crawl-selenium\\1117bsc
download_html_and_images_with_selenium(base_path)
