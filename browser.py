import webbrowser
import urllib.parse

class BrowserControl:
    def open_url(self, url):
        webbrowser.open(url)
        print(f"✅ 已打开：{url}")

    def search(self, query, engine="bing"):
        # URL 编码，防止空格和特殊符号导致浏览器解析崩溃
        safe_query = urllib.parse.quote(query)
        
        # 🌐 多模态搜索引擎矩阵 (bing 为基础底座，修正全部字典语法错误)
        search_engines = {
            "bing": f"https://www.bing.com/search?q={safe_query}",
            "google": f"https://www.google.com/search?q={safe_query}",
            "baidu": f"https://www.baidu.com/s?wd={safe_query}",
            "duckduckgo": f"https://duckduckgo.com/?q={safe_query}",
            "sogou": f"https://www.sogou.com/web?query={safe_query}",
            "bilibili": f"https://search.bilibili.com/all?keyword={safe_query}",
            "github": f"https://github.com/search?q={safe_query}",
            "youtube": f"https://www.youtube.com/results?search_query={safe_query}",
            "huggingface": f"https://huggingface.co/models?search={safe_query}",
            "reddit": f"https://www.reddit.com/search/?q={safe_query}",
            "taobao": f"https://s.taobao.com/search?q={safe_query}",
            "jd": f"https://search.jd.com/Search?keyword={safe_query}",
            "amazon": f"https://www.amazon.com/s?k={safe_query}",
            "ebay": f"https://www.ebay.com/sch/i.html?_nkw={safe_query}",
            "shein": f"https://us.shein.com/pdsearch/{safe_query}",
            "temu": f"https://www.temu.com/search_result.html?search_key={safe_query}",
            "x": f"https://x.com/search?q={safe_query}",
            "xiaohongshu": f"https://www.xiaohongshu.com/search_result?keyword={safe_query}"
        }
        
        # 获取匹配的引擎 URL，如果找不到，兜底使用 bing
        url = search_engines.get(engine.lower(), search_engines["bing"])
        self.open_url(url)