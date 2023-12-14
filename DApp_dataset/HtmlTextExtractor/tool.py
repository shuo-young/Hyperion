import bs4
from selenium import webdriver
import re
from transformers import LlamaTokenizer
import sys

cur_id = 0

def split_text(text, max_tokens=3000):
    tokenizer = LlamaTokenizer.from_pretrained('.\\dir')
    tokens = tokenizer.tokenize(text)
    segments = []

    for i in range(0, len(tokens), max_tokens):
        segment_tokens = tokens[i:i+max_tokens]
        segment = tokenizer.convert_tokens_to_string(segment_tokens)
        segments.append(segment)

    return segments

def crawl(url):
    #下面这些设置比如不加载图片，不启动浏览器，是为了加快爬取速度
    chrome_options = webdriver.ChromeOptions()

    prefs = {
        'profile.default_content_setting_values': {
            'images': 2,  # 禁用图片的加载
            'css': 2,  # 禁用图片的加载
        }
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument('blink-settings=imagesEnabled=false')
    chrome_options.add_argument("window-size=1024,768")
    chrome_options.add_argument('--headless')

    driver = webdriver.Chrome(options=chrome_options)

    #根据链接爬取网页的html代码
    html_str = ''
    try:
        driver.get(url)
        html_str = driver.page_source
    except:
        print('There are some errors while crawling the website')
        raise Exception()
    finally:
        driver.quit()

    return html_str

def copy(text):
    global cur_id
    cur_id += 1

    #去掉text里面的乱码
    text = re.sub(r'[^A-Za-z0-9`~!@#$%^&*()_\-+=<>?:"{}|,.\/;\'\[\]·~！@#￥%……&*（）——\-+={}|《》？：“”【】、；‘，。、 ]', '', text)

    #把text里面的双引号改为单引号
    text = re.sub(r'\"', '\'', text)

    #把text里面多个连在一起的空格去掉
    text = re.sub(r'[ ]{2,}', ' ', text)

    #获取分段后的内容
    segments = split_text(text)

    content = '['
    for i, segment in enumerate(segments):
        #添加JSON对象的格式（前半部分
        content += '\n\t{\n\t\t\"input\": \"'

        #添加input的内容
        content = content + segment + '\",'
        #添加id
        content = content + '\n\t\t\"id\": \"' + str(cur_id)+'\"'

        #添加JSON对象的格式（后半部分
        content += '\n\t},'
    content = content[:-1]
    content += '\n]'

    with open('result\\test.json', 'w', encoding='utf-8') as f:
        f.write(content)

def create_json_file(html_str):
    soup = bs4.BeautifulSoup(html_str, 'html.parser')

    # 提取<body>标签内的所有文本
    body_text = soup.body.get_text(strip=True)
    copy(body_text)

def main():
    url = sys.argv[1] if len(sys.argv) > 1 else ''
    
    if url == '':
        print('You should input a non-empty url')
        return
    try:
        html_str = crawl(url)
    except:
        print('Please check your url')
        return
    
    create_json_file(html_str)
    print('Success!')
    

if __name__ == '__main__':
    main()
