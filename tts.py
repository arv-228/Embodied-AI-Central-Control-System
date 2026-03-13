import os
import time
import threading
import subprocess
import queue
import pygame  # 依然使用游戏级静默混音器

try:
    import pyttsx3 
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

class TextToSpeech:
    def __init__(self):
        self.name = "小智"
        self.language = "mandarin" 
        
        # 🚨 史诗级进化：引入线程安全的语音播报队列
        self.tts_queue = queue.Queue()
        
        pygame.mixer.init()
        
        if HAS_PYTTSX3:
            self.offline_engine = pyttsx3.init()
            self.offline_engine.setProperty('rate', 150)
        else:
            self.offline_engine = None
            
        # 🚨 启动专属的 TTS 后台消费线程，随主程序同生共死
        threading.Thread(target=self._tts_worker, daemon=True).start()

    def set_name(self, name):
        self.name = name

    def set_language(self, lang):
        self.language = lang

    def _get_edge_voice(self):
        if self.language == "cantonese":
            return "zh-HK-HiuMaanNeural"
        elif self.language == "english":
            return "en-US-AriaNeural"
        else:
            return "zh-CN-XiaoxiaoNeural"

    def speak(self, text):
        """生产者：只负责将文本极速入队，绝不阻塞主线程，绝不吞没任何一句话"""
        if not text:
            return
        self.tts_queue.put(text)

    def _tts_worker(self):
        """消费者：独立的音频排队执行线程，保证按顺序播报"""
        while True:
            # 阻塞等待新的播报任务，没有任务时挂起，不占 CPU
            text = self.tts_queue.get() 
            
            voice = self._get_edge_voice()
            output_file = f"temp_speech_{int(time.time())}.mp3"
            
            print(f"🔊 语音播报 ({voice}): {text}")
            
            try:
                cmd = f'edge-tts --voice {voice} --text "{text}" --write-media {output_file}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(output_file):
                    pygame.mixer.music.load(output_file)
                    pygame.mixer.music.play()
                    
                    # 循环检查是否播放完毕
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                        
                    # 必须 unload 才能解除文件占用
                    pygame.mixer.music.unload()
                    time.sleep(0.1)
                    
                    try:
                        os.remove(output_file)
                    except Exception:
                        pass
                else:
                    raise Exception("Edge-TTS 网络请求失败或文件未生成")
                    
            except Exception as e:
                print(f"⚠️ 在线语音崩溃 ({e})，触发离线 pyttsx3 备用引擎...")
                if self.offline_engine:
                    self.offline_engine.say(text)
                    self.offline_engine.runAndWait()
                else:
                    print("❌ 未安装 pyttsx3 离线引擎，小智失去发声能力。")
            finally:
                # 标记该任务已完成，队列继续处理下一个
                self.tts_queue.task_done()