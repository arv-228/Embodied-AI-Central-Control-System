# page_parser.py
import re
import requests
from bs4 import BeautifulSoup

class PageParser:
    def extract_text(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return " ".join(chunk for chunk in chunks if chunk)

    def get_page_text(self, url):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return self.extract_text(response.text)
            else:
                return f"❌ 网页加载失败：{response.status_code}"
        except Exception as e:
            return f"❌ 请求失败：{e}"
