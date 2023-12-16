import bs4
from selenium import webdriver
import re
from transformers import LlamaTokenizer
import sys

cur_id = 0


def split_text(text, max_tokens=3000):
    tokenizer = LlamaTokenizer.from_pretrained(".\\dir")
    tokens = tokenizer.tokenize(text)
    segments = []

    for i in range(0, len(tokens), max_tokens):
        segment_tokens = tokens[i : i + max_tokens]
        segment = tokenizer.convert_tokens_to_string(segment_tokens)
        segments.append(segment)

    return segments


def crawl(url):
    chrome_options = webdriver.ChromeOptions()

    prefs = {
        "profile.default_content_setting_values": {
            "images": 2,
            "css": 2,
        }
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("blink-settings=imagesEnabled=false")
    chrome_options.add_argument("window-size=1024,768")
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)

    html_str = ""
    try:
        driver.get(url)
        html_str = driver.page_source
    except:
        print("There are some errors while crawling the website")
        raise Exception()
    finally:
        driver.quit()

    return html_str


def copy(text):
    global cur_id
    cur_id += 1

    text = re.sub(
        r'[^A-Za-z0-9`~!@#$%^&*()_\-+=<>?:"{}|,.\/;\'\[\]·~！@#￥%……&*（）——\-+={}|《》？：“”【】、；‘，。、 ]',
        "",
        text,
    )

    text = re.sub(r"\"", "'", text)

    text = re.sub(r"[ ]{2,}", " ", text)

    segments = split_text(text)

    content = "["
    for i, segment in enumerate(segments):
        content += '\n\t{\n\t\t"input": "'

        content = content + segment + '",'

        content = content + '\n\t\t"id": "' + str(cur_id) + '"'

        content += "\n\t},"
    content = content[:-1]
    content += "\n]"

    with open("result\\test.json", "w", encoding="utf-8") as f:
        f.write(content)


def create_json_file(html_str):
    soup = bs4.BeautifulSoup(html_str, "html.parser")

    body_text = soup.body.get_text(strip=True)
    copy(body_text)


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else ""

    if url == "":
        print("You should input a non-empty url")
        return
    try:
        html_str = crawl(url)
    except:
        print("Please check your url")
        return

    create_json_file(html_str)
    print("Success!")


if __name__ == "__main__":
    main()
