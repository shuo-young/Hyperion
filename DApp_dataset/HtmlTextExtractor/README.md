# HtmlTextExtractor

## Description

A tool for extracting text content from web pages.



## Functions

- Web crawling
  - The tool will first crawl the specified web page.
- Json file generation
  - After crawling, the tool extracts the text content of the web page and uses the llama word segmenter to segment the text. Finally, based on the segmentation results, the json file corresponding to the web page is generated in the "result" directory for subsequent large model testing.



## Usage

1. Prepare requirements.

- Python environment: please use Python 3.8, which is recommended (tested).
- Python dependencies: please use pip to install dependencies in `requirements.txt`.

```
$ pip3 install -r requirements.txt
```



2. Parameter

- Running the program requires only one parameter 

```
$ python tool.py [url]
```



3. Example

```
$ python tool.py "https://www.example.com/"
```

