import cv2
import numpy as np
try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    from rapidocr_onnxruntime import RapidOCR
    HAS_OCR = True
except Exception:
    RapidOCR = None
    HAS_OCR = False

class ScreenParser:
    def __init__(self):
        # OCR 引擎：如果 onnxruntime 不可用则降级为无视觉模式
        if HAS_OCR:
            try:
                self.ocr = RapidOCR()
            except Exception as e:
                print(f"⚠️ OCR 引擎初始化失败，视觉点击功能不可用: {e}")
                self.ocr = None
        else:
            print("⚠️ rapidocr_onnxruntime 不可用，click_text 功能已禁用")
            self.ocr = None
        self.sct = None
        self.logger = None

    def set_logger(self, logger_func):
        self.logger = logger_func

    def _log(self, msg):
        if self.logger:
            self.logger(msg)
        else:
            print(msg)

    def _get_sct(self):
        """懒加载获取 mss 实例，只有在真正需要看屏幕的瞬间才去挂载系统显示器"""
        if self.sct is None:
            self.sct = mss.mss()
        return self.sct

    def find_text_and_click_coords(self, target_text):
        if self.ocr is None:
            self._log("❌ OCR 引擎不可用，无法执行 click_text 动作")
            return None   
        """全屏扫描并返回目标文字的中心坐标 (X, Y)"""
        self._log(f"👀 视觉皮层已启动，正在全屏搜索: [{target_text}]")
        
        try:
            # 1. 极速全屏截图 (调用懒加载模块)
            sct_instance = self._get_sct()
            monitor = sct_instance.monitors[1]  # 抓取主屏幕
            screenshot = np.array(sct_instance.grab(monitor))
            img = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
            
            # 2. OCR 矩阵扫描
            result, _ = self.ocr(img)
            if not result:
                self._log("⚠️ 视野内未发现任何文字。")
                return None
            
            # 🚨 优化第一层：【精确匹配】优先狙击
            for box, text, score in result:
                if text.strip().lower() == target_text.strip().lower():
                    x_center = int((box[0][0] + box[2][0]) / 2) + monitor["left"]
                    y_center = int((box[0][1] + box[2][1]) / 2) + monitor["top"]
                    self._log(f"🎯 视觉精确锁定！完美命中 [{target_text}] 坐标为: (X:{x_center}, Y:{y_center})")
                    return (x_center, y_center)

            # 🚨 优化第二层：【宽松匹配】降级搜索
            for box, text, score in result:
                if target_text.lower() in text.lower() or text.lower() in target_text.lower():
                    x_center = int((box[0][0] + box[2][0]) / 2) + monitor["left"]
                    y_center = int((box[0][1] + box[2][1]) / 2) + monitor["top"]
                    self._log(f"🎯 视觉模糊锁定！目标 [{target_text}] 命中屏幕元素 [{text}]，坐标为: (X:{x_center}, Y:{y_center})")
                    return (x_center, y_center)
            
            self._log(f"⚠️ 视野内未找到目标: [{target_text}]")
            return None
            
        except Exception as e:
            self._log(f"❌ 视觉解析崩溃: {e}")
            return None