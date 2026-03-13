Embodied AI Central Control SystemEmbodied AI Central is a sophisticated digital entity hub designed to 
bridge the gap between Large Vision-Language Models (VLM) and native Windows environments. 
It functions as an autonomous agent that can see through a camera, perceive screen contents via OCR, 
listen to voice commands, and act by controlling system UI components.


🚀 Key Capabilities👁️ Visual Intelligence: 
Real-time human pose estimation using YOLOv8-pose (functioning as a "vision radar") and high-fidelity screen parsing via RapidOCR.


🧠 Hybrid Brain: 
Supports seamless switching between local GGUF models (via llama-cpp), 
HuggingFace Transformers, and specialized Vision-Language Models like Qwen-VL.


🦾 Multi-Layer RPA Engine:
Native Control: High-precision window manipulation via pywinauto.
Visual Anchoring: Text-based UI interaction (click-by-text) using OCR coordinates.
Direct Input: Low-level peripheral emulation via pyautogui.


🎙️ Multimodal Interaction:
Speech-to-Text: Real-time STT supporting English, Mandarin, and Cantonese.
Neural TTS: High-quality voice synthesis via Edge-TTS with an offline pyttsx3 fallback.


🧩 Skill Extensibility:
A unique .skill system allows users to define new complex workflows using Markdown and YAML frontmatter.


🏗️ Technical Architecture
graph TD

    Main[Main Controller] --> GUI[PyQt5 Fluent UI]
    Main --> Brain[VLM Manager]
    Main --> Vision[Camera & OCR Engine]
    Main --> Voice[STT & TTS System]
    Main --> RPA[Automation Engine]
    Vision --> YOLO[YOLOv8-Pose Radar]
    Vision --> OCR[RapidOCR Screen Parser]
    RPA --> Win32[Native Win32 API]
    RPA --> Input[Input Simulation]

    
📂 Repository Structure

Module------------Files------------------------------------Description

Main Logic--------main.py----------------------------------Orchestrates the lifecycle of all AI subsystems.

UI Layer----------gui.py-----------------------------------Modern PyQt5 dashboard with system monitoring.

Automation--------automation.py----------------------------The RPA core handling window & mouse/keyboard logic.

Vision------------camera.py, screen_parser.py--------------Pose tracking and screen content extraction.

AI Brain----------embodied_ai_model.py---------------------Adapter for various VLM and LLM backends.

Management--------skill_manager.py, resource_manager.py----Plugin loading and hardware resource optimization.



🛠️ Installation & Setup
1. RequirementsOS:
   
   Windows 10/11 (Required for RPA/Win32 features).
   Hardware: 8GB+ RAM, NVIDIA GPU (Recommended for VLM inference).
   
2. Environment Setup
   
Bash# Clone the repository
git clone https://github.com/arv-228/Embodied-AI-Central-Control-System.git

cd Embodied-AI-Central-Control-System

Install dependencies
pip install -r requirements.txt

3. Model Preparation
   
Ensure yolov8n-pose.pt is in the root directory.
Place your .gguf or HuggingFace model weights in the models/ directory.

4. Running
   Bash
   python main.py
   
🔧 Troubleshooting

COM Threading Issues

The project uses pywinauto for window control. Since PyQt5 operates on a Single Threaded Apartment (STA) model, we've implemented a delayed import strategy for pywinauto inside worker threads to prevent CoInitialize conflicts.

Debugging

If you encounter module import errors, run the diagnostic script:

Bash
python debug_imports.py

📜 LicenseDistributed under the AGPL-3.0 License. See LICENSE for more information.


Embodied AI Central (具身智能中央控制系统)Embodied AI Central 是一个高度集成的数字生命中枢。

它不仅是一个 AI 聊天机器人，更是一个具备视觉感知、听觉反馈、意图理解以及原生系统执行能力的具身智能体。

它能“看”到你的屏幕，理解你的语音指令，并像真人一样通过鼠标和键盘操作 Windows 程序。

🚀 核心技术栈

👁️ 视觉雷达 (Vision)：基于 YOLOv8-pose 的人体骨骼追踪（隐形雷达）与 RapidOCR 实时屏幕解析。

🧠 智能决策 (Brain)：统一多模态适配层，支持 Transformers (VLM)、Llama-cpp (GGUF 本地推理) 以及 Qwen-VL。

🦾 自动化控制 (RPA)：采用三层控制架构（pywinauto 原生控件、RapidOCR 视觉定位、pyautogui 底层驱动）。

🎙️ 交互系统 (Interaction)：

语音：支持 Google/Edge 语音识别（中/英/粤）。

播报：Edge-TTS 神经网络语音 + pyttsx3 本地离线备份。

UI：基于 PyQt5 的现代化半透明交互界面。


🏗️ 项目模块概览

模块名称----核心文件----功能描述

主控中枢----main.py----协调视觉、语音、大脑与 RPA 的逻辑闭环。

视觉雷达----camera.py----实时捕捉摄像头画面，进行人体姿态感应。

自动化引擎----automation.py----执行点击、输入、截图等系统级操作。

多模态大脑----embodied_ai_model.py----适配各类 VLM 大模型，进行逻辑推理与视觉分析。

技能库系统----skill_manager.py----允许用户通过 .skill 文件扩展 AI 的操作能力。

权限指纹----permissions.py----基于设备指纹的全局权限管理系统。

🛠️ 快速部署
1. 克隆与环境配置
   
   Bash
   
   git clone https://github.com/your-username/EmbodiedAI-Central.git
   
   cd EmbodiedAI-Central
   
   pip install -r requirements.txt
   
3. 准备模型权重请确保以下文件位于根目录或 models/ 文件夹：
   
   yolov8n-pose.pt (根目录)
   
   你选择的大模型 (例如 qwen-7b-vlm.gguf 放入 models/)

4. 运行程序
   
   Bash
   
   python main.py
   
💡 特色功能：Skill 扩展系统

本项目支持通过编写简单的 SKILL.md 来教 AI 学习新的复杂流程：

创建一个文件夹 my_skill/。

放入 SKILL.md，使用 YAML 定义触发场景。

程序启动时会自动扫描并注入 AI 的“系统提示词”中。

🛡️ 开源协议本项目采用 AGPL-3.0 协议开源。由于具备屏幕监控与系统控制能力，请在法律允许的范围内使用。
