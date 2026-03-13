import speech_recognition as sr
import time

class VoiceRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # 优化参数：降低 pause_threshold 提高响应速度
        self.recognizer.pause_threshold = 1.2
        self.recognizer.dynamic_energy_threshold = True
        
        with self.microphone as source:
            print("🎤 初始化环境中...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def listen_for_wake_word(self, lang="zh-CN"):
        """根据语种动态切换唤醒词：中文/粤语->小智, 英语->Tom"""
        # 1. 定义不同语种的唤醒词
        CN_WAKE_WORDS = ["小智", "小志", "晓志"] # 增加同音词容错
        EN_WAKE_WORDS = ["tom", "thomas", "hey tom"] # 增加 Tom 的变体

        with self.microphone as source:
            try:
                # 动态环境补偿
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                print(f"👂 [{lang}] 待命中...")
                
                audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=8)
                text = self.recognizer.recognize_google(audio, language=lang)
                print(f"🎤 原始识别: {text}")

                is_wakened = False
                command = ""

                # 2. 分支逻辑：中文 & 粤语
                if lang.startswith("zh"):
                    for kw in CN_WAKE_WORDS:
                        if kw in text:
                            is_wakened = True
                            command = text.split(kw)[-1].strip()
                            break

                # 3. 分支逻辑：英语 (强制转小写匹配)
                else:
                    text_lower = text.lower()
                    for kw in EN_WAKE_WORDS:
                        if kw in text_lower:
                            is_wakened = True
                            command = text_lower.split(kw)[-1].strip()
                            break

                # 4. 统一唤醒处理
                if is_wakened:
                    if not command:
                        print(f"✨ {'Tom' if lang=='en-US' else '小智'} 正在听，请下令...")
                        # 补录指令
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=8)
                        command = self.recognizer.recognize_google(audio, language=lang)
                    return command

            except (sr.UnknownValueError, sr.WaitTimeoutError):
                return None
            except Exception as e:
                # print(f"识别异常: {e}")
                return None
        return None