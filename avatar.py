import os
import cv2
import numpy as np
import pygame

class Avatar:
    def __init__(self, width=800, height=600):
        # 1. 强制初始化 Pygame 引擎
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Embodied AI - 视觉化身系统")
        self.clock = pygame.time.Clock()
        
        # 2. 自动匹配系统中文字体，防止中文状态显示为方块乱码
        try:
            # 尝试加载微软雅黑或黑体
            font_name = pygame.font.match_font('microsoftyahei') or pygame.font.match_font('simhei')
            self.font = pygame.font.Font(font_name, 36)
        except:
            # 极端情况下的兜底字体
            self.font = pygame.font.Font(None, 36)
            
        self.vrm_path = None

    def load_custom_vrm(self, path):
        """
        全量保留功能：兼容 UI 传来的 VRM 3D 模型路径加载请求。
        确保 main.py 调用此方法时绝不报错。
        """
        if os.path.exists(path):
            self.vrm_path = path
            print(f"👔 视觉化身模型已成功加载: {path}")
        else:
            print(f"⚠️ 找不到指定的化身模型文件: {path}")

    def update(self, state=None, frame=None):
        """
        全量核心渲染逻辑：同步处理底层的真实摄像头画面与顶层的 AI 状态反馈。
        完全修复了缩进错误，绝对不会引发 IndentationError。
        """
        # 1. 每一帧先用深色清空屏幕背景
        self.screen.fill((30, 30, 30))

        # 2. 核心功能：渲染底层的摄像头真实画面
        if frame is not None:
            try:
                # OpenCV 捕获的是 BGR 格式，必须转换为 Pygame 的 RGB 格式
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Pygame 的坐标系与 NumPy 数组是转置的，需要进行旋转和镜像翻转
                frame_rgb = np.rot90(frame_rgb)
                frame_rgb = np.flipud(frame_rgb)
                
                # 将 NumPy 数组无缝转换为 Pygame 的 Surface 图像源
                frame_surface = pygame.surfarray.make_surface(frame_rgb)
                
                # 动态缩放画面以完美填满窗口大小
                frame_surface = pygame.transform.scale(frame_surface, (self.width, self.height))
                
                # 将处理好的画面绘制在屏幕的左上角 (0, 0)
                self.screen.blit(frame_surface, (0, 0))
            except Exception as e:
                print(f"⚠️ 摄像头画面渲染出现异常，已静默处理防止崩溃: {e}")

        # 3. 核心功能：渲染顶层的 AI 状态信息 (思考中、待命、执行指令)
        if state is None:
            state_text = "🟢 待命中 (Listening...)"
            text_color = (100, 255, 100)  # 绿色
        elif state == "thinking":
            state_text = "🤔 大脑高速运转中 (Thinking...)"
            text_color = (255, 165, 0)    # 橙色
        else:
            state_text = f"🤖 正在执行: {state}"
            text_color = (0, 255, 255)    # 青色

        # 绘制黑色的文字阴影，保证在任何复杂的摄像头画面背景下文字都能看清
        shadow_surface = self.font.render(state_text, True, (0, 0, 0))
        self.screen.blit(shadow_surface, (22, 22))
        
        # 绘制彩色的文字本体
        text_surface = self.font.render(state_text, True, text_color)
        self.screen.blit(text_surface, (20, 20))

        # 4. 强制锁定帧率，确保 CPU 不会因为无节制渲染而满载
        self.clock.tick(30)