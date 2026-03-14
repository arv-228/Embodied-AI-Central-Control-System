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
   Python 3.12 (Required for environment）
   Hardware: 4GB+ RAM, NVIDIA GPU (Recommended for VLM inference).
   
3. Environment Setup
   
Bash# 
Clone the repository

git clone https://github.com/arv-228/Embodied-AI-Central-Control-System.git

cd Embodied-AI-Central-Control-System

Install dependencies
py -3.12 -m pip install -r requirements.txt

3. Model Preparation
   
Ensure yolov8n-pose.pt is in the root directory.
Place your .gguf or HuggingFace model weights in the models/ directory.

4. Running
   Bash
   py -3.12 main.py
   
🔧 Troubleshooting

COM Threading Issues

The project uses pywinauto for window control. Since PyQt5 operates on a Single Threaded Apartment (STA) model, we've implemented a delayed import strategy for pywinauto inside worker threads to prevent CoInitialize conflicts.

Debugging

If you encounter module import errors or main.py error, run the diagnostic script:

Bash
py -3.12 debug_imports.py
py -3.12 debug_main.py

📜 LicenseDistributed under the AGPL-3.0 License. See LICENSE for more information.


Embodied AI Central (具身智能中央控制系统)Embodied AI Central 是一个高度集成的数字生命中枢。

它不仅是一个 AI 聊天机器人，更是一个具备视觉感知、听觉反馈、意图理解以及原生系统执行能力的具身智能体。

它能“看”到你的屏幕，理解你的语音指令，并像真人一样通过鼠标和键盘操作 Windows 程序。



🚀 核心技术栈

👁️ 视觉雷达 (Vision)：集成 YOLOv8-pose 实时人体骨骼追踪（隐形雷达）与 RapidOCR 屏幕识字，能够感知物理环境并解析电脑屏幕内容。


🧠 智能决策 (Brain)：统一适配主流 VLM 架构，支持 Transformers、Llama-cpp (GGUF 本地推理) 以及 Qwen-VL 系列模型。


🦾 三层 RPA 自动化架构：

原生 Win32 层：基于 pywinauto 精准控制系统窗口和控件。

视觉层：通过 OCR 识别 UI 文本实现“所见即所得”的点击。

模拟层：使用 pyautogui 作为底层逻辑兜底，模拟真实的硬件输入。


🎙️ 实时交互系统：支持中、英、粤三语识别，配备 Edge-TTS 神经网络语音与 pyttsx3 离线双引擎。


🛠️ 技能 (Skill) 扩展系统：支持用户通过编写简单的 SKILL.md（含 YAML 元数据）来教 AI 学习新的复杂指令流程。


⚖️ 资源监控器：内置资源管理器实时监控 CPU/GPU/RAM，在高负载下自动清理缓存，确保系统运行平稳。




📂 模块文件说明

文件名-----描述

main.py-----程序主入口，负责视觉、语音、大脑与 RPA 的逻辑闭环调度。

gui.py-----基于 PyQt5 的现代化交互界面，支持深色/浅色模式切换。

automation.py-----核心自动化执行引擎，处理复杂的 RPA 逻辑。

camera.py-----视觉采集模块，负责摄像头流处理与 YOLO 姿态感应。

embodied_ai_model.py-----大模型适配层，将用户意图转化为可执行的 JSON 指令。

skill_manager.py-----技能插件管理器，自动扫描并注入本地 Skill 到 AI 大脑。

permissions.py-----基于设备指纹的全局权限管理系统，确保安全受控。

resource_manager.py-----硬件资源监控，防止大模型推理导致系统宕机。




🛠️ 快速部署
环境要求:（注：本项目涉及多线程 COM 操作，建议在 Windows 环境下运行）
   
   系统：Windows 10/11 (Required for RPA/Win32 features).
   语音：Python 3.12 
   硬件: 4GB+ RAM, NVIDIA GPU (Recommended for VLM inference).


1. 克隆与环境配置 
   
   Bash
   
   git clone https://github.com/your-username/EmbodiedAI-Central.git
   
   cd EmbodiedAI-Central
   
   py -3.12 -m pip install -r requirements.txt
   
3. 准备模型权重请确保以下文件位于根目录或 models/ 文件夹：
   
   yolov8n-pose.pt (根目录)
   
   你选择的大模型 (例如 qwen-7b-vlm.gguf 放入 models/)

4. 运行程序
   
   Bash
   
   py -3.12 main.py
   
💡 特色功能：Skill 扩展系统

本项目支持通过编写简单的 SKILL.md 来教 AI 学习新的复杂流程：

你只需在任意位置创建一个文件夹（如 my_skill/），并在其中放入 SKILL.md：

    Markdown
    ---
    name: 自动打卡
    description: 当我说“帮我打卡”时，执行此流程
    ---
    1. 运行 "C:\Program Files\WorkApp.exe"
    2. 点击屏幕上的 "立即签到" 按钮
    3. 截图保存到桌面


系统启动时会自动扫描并学习该技能，无需修改核心代码。



🔧 技术避坑指南 (Troubleshooting)
COM 线程冲突：由于 PyQt5 使用 STA 模型，而 pywinauto 默认可能触发 MTA。在代码中通过延迟动态导入解决了这一冲突，请勿在 automation.py 的文件顶部直接 import pywinauto。

视觉定位偏移：如果遇到点击不准，请检查 Windows 系统缩放比例（DPI）。在 main.py 中通过 ctypes 开启了进程级 DPI 感知。

静默权限校验：系统会自动生成 permission_agreed.dat。如果更换了电脑，需重新同意权限协议以生成新的设备指纹。

除错指令：
如果发生了载入模块错误或主控程序出错，执行下面分析命令：

Bash
py -3.12 debug_imports.py
py -3.12 debug_main.py


🛡️ 开源协议本项目采用 AGPL-3.0 协议开源。由于具备屏幕监控与系统控制能力，请在法律允许的范围内使用。







AI Models Type 


Pytorch Version (included config.json) (Recommend)


GGUF Version now is not support with Qwen 3.5 Visual Version




接入AI 模型类型


Pytorch 版本 （带有config.json的模型）（推荐）


GGUF版本暂时不支持Qwen 3.5 视觉多模态版本
