# ai_generator.py
import random
import re

class AIGenerator:
    def __init__(self):
        self.templates = {
            "Python": [
                "def hello():\n    print('Hello, world!')",
                "x = 10\ny = 20\nprint(x + y)",
                "import numpy as np\narr = np.array([1,2,3])\nprint(arr)",
            ],
            "JavaScript": [
                "function greet(name) {\n    console.log('Hello, ' + name);\n}",
                "let a = 10;\nlet b = 20;\nconsole.log(a + b);",
            ],
            "HTML": [
                "<h1>欢迎使用 AI 生成页面</h1>",
                "<p>这是一个由 AI 生成的网页</p>",
            ],
        }

    def generate_code(self, language="Python", prompt=""):
        if language in self.templates:
            return random.choice(self.templates[language])
        else:
            return "❌ 未找到该语言模板"

    def generate_code_by_prompt(self, prompt):
        if "Python" in prompt:
            return self.generate_code("Python", prompt)
        elif "JavaScript" in prompt:
            return self.generate_code("JavaScript", prompt)
        elif "HTML" in prompt:
            return self.generate_code("HTML", prompt)
        else:
            return "请指定语言（如 Python、JavaScript）"

    def preview_code(self, code, language="Python"):
        print(f"\n📋 生成代码预览（{language}）：")
        print(f"```{language}\n{code}\n```")
