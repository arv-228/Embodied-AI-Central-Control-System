# code_detector.py
import re

class CodeDetector:
    def detect_code(self, text):
        patterns = {
            "python": r"```python.*?```",
            "javascript": r"```js.*?```",
            "html": r"<html>.*?</html>",
        }
        for lang, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return f"✅ 发现 {lang} 代码：\n{match.group()}"
        return "❌ 未发现代码"
