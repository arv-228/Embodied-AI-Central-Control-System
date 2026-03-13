import os
import json
import ctypes
import string
import datetime
import gc
import cv2
import base64
from PIL import Image
import torch
import re
from transformers import (
    AutoTokenizer, 
    AutoProcessor, 
    AutoModelForCausalLM, 
    BitsAndBytesConfig
)

try:
    from llama_cpp import Llama
    from llama_cpp.llama_chat_format import Llava15ChatHandler
except ImportError:
    Llama = None
    Llava15ChatHandler = None

try:
    from qwen_vl_utils import process_vision_info as _qwen_process_vision_info
except ImportError:
    _qwen_process_vision_info = None

# ============================================================
#  🚀 通用 VL 适配层 (Universal Vision-Language Adapter)
#  支持市面上所有主流 VLM 架构，新架构只需在此处登记即可
# ============================================================

# GGUF 视觉架构：架构名 → llama_cpp chat_handler 类名
GGUF_VL_HANDLERS = {
    # ── LLaVA 系列 ──
    "llava":            "Llava15ChatHandler",
    "llava16":          "Llava16ChatHandler",
    "llava_phi3":       "LlavaPhiChatHandler",
    # ── Qwen-VL 系列（含 Qwen3.5）──
    "qwenvl":           "Qwen2VLChatHandler",
    "qwen2vl":          "Qwen2VLChatHandler",
    "qwen3vl":          "Qwen2VLChatHandler",
    "qwen3.5":          "Qwen2VLChatHandler",   
    "qwen2.5vl":        "Qwen2VLChatHandler",
    # ── MiniCPM-V 系列 ──
    "minicpmv":         "MiniCPMv26ChatHandler",
    "minicpm-v":        "MiniCPMv26ChatHandler",
    "minicpm_v":        "MiniCPMv26ChatHandler",
    # ── 其他常见 VL ──
    "moondream":        "MoondreamChatHandler",
    "obsidian":         "ObsidianChatHandler",
    "internvl":         "Llava15ChatHandler",   
    "phi3v":            "LlavaPhiChatHandler",
    "phi-3-vision":     "LlavaPhiChatHandler",
}

# PyTorch 视觉架构识别关键字 → 图像注入方式
VL_ARCH_STRATEGY = {
    "qwen2vlforconditionalgeneration":   "qwen2vl",
    "qwen3vlforconditionalgeneration":   "qwen2vl",
    "qwenvlforconditionalgeneration":    "qwen2vl",
    "qwen3_5_vl":                        "qwen2vl",
    "qwen2_5_vl":                        "qwen2vl",
    "qwen3.5":                           "qwen2vl",
    "llavaforconditionalgeneration":                  "standard",
    "llava_next":                                     "standard",
    "llavaonevisionforconditionalgeneration":         "standard",
    "llavanextvideoforcausallm":                      "standard",
    "ideficsforvisualtextgeneration":                 "idefics",
    "idefics2forconditionalgeneration":               "idefics",
    "idefics3forconditionalgeneration":               "idefics",
    "paligemmaforconditionalgeneration":              "standard",
    "minicpmv":                                       "standard",
    "minicpm_v":                                      "standard",
    "internvlchatmodel":                              "standard",
    "internlm2forcausallm":                           "standard", 
    "phi3vforcausallm":                               "standard",
    "phi3smallv":                                     "standard",
    "moondreambatchimageprocessor":                   "standard",
    "florence2forcausallm":                           "standard",
    "smolvlmforconditionalgeneration":                "standard",
    "gotocr2forcausallm":                             "standard",
    "deepseekVLv2forcausallm":                        "standard",
    "ristrettovlmforcausallm":                        "standard",
}

VL_LOAD_PREFER_VISION2SEQ = {
    "qwen2vlforconditionalgeneration",
    "qwen3vlforconditionalgeneration",
    "qwenvlforconditionalgeneration",
    "llavaforconditionalgeneration",
    "llavaonevisionforconditionalgeneration",
    "idefics2forconditionalgeneration",
    "idefics3forconditionalgeneration",
    "paligemmaforconditionalgeneration",
    "smolvlmforconditionalgeneration",
    "florence2forcausallm",
}

def _get_gguf_vl_handler(model_name_lower, model_dir):
    """为 GGUF VL 模型自动匹配 chat_handler"""
    if Llama is None:
        return None, False

    mmproj_path = None
    try:
        mmproj_path = next(
            (os.path.join(model_dir, f) for f in os.listdir(model_dir)
             if "mmproj" in f.lower() and f.lower().endswith(".gguf")),
            None
        )
    except Exception:
        pass

    if not mmproj_path:
        return None, False  

    handler_cls = None
    for keyword, cls_name in GGUF_VL_HANDLERS.items():
        if keyword in model_name_lower:
            try:
                from llama_cpp import llama_chat_format as _lcf
                handler_cls = getattr(_lcf, cls_name, None)
            except Exception:
                pass
            if handler_cls:
                break

    if handler_cls is None:
        try:
            from llama_cpp.llama_chat_format import Llava15ChatHandler as _fallback
            handler_cls = _fallback
            print(f"⚠️ 未识别到具名 VL handler，使用 LLaVA 1.5 通用兜底")
        except Exception:
            return None, False

    try:
        handler = handler_cls(clip_model_path=mmproj_path, verbose=False)
        print(f"👁️ GGUF 视神经挂载成功: {os.path.basename(mmproj_path)}")
        return handler, True
    except Exception as e:
        print(f"⚠️ GGUF 视神经挂载失败: {e}")
        return None, False

def _detect_pytorch_vl_strategy(arch_name: str, model_type: str, processor) -> str:
    """检测 PyTorch VL 模型图像注入策略"""
    arch_lower = arch_name.lower().replace("-", "_").replace(".", "_")
    type_lower = model_type.lower().replace("-", "_").replace(".", "_")

    for key, strategy in VL_ARCH_STRATEGY.items():
        if key in arch_lower:
            return strategy

    for key, strategy in VL_ARCH_STRATEGY.items():
        if key in type_lower:
            return strategy

    combined = arch_lower + " " + type_lower
    if any(kw in combined for kw in ["qwenvl", "qwen_vl", "qwen2vl", "qwen3vl", "qwen2_5_vl", "qwen3_5_vl"]):
        return "qwen2vl"
    if "idefics" in combined:
        return "idefics"
    
    vl_keywords = ["vision", "llava", "minicpm", "internvl", "phi3v", "moondream", "paligemma", "florence", "smolvlm", "deepseek_vl"]
    if any(kw in combined for kw in vl_keywords):
        if hasattr(processor, "image_processor"):
            return "standard"

    if hasattr(processor, "image_processor") and "vl" in type_lower:
        return "standard"

    return ""  

class LocalModelManager:
    def __init__(self):
        self.model_instance = None
        self.processor = None
        self.engine_type = None
        self.has_vision = False
        self.vl_strategy = ""       
        self.found_models_dict = {}
        self.conversation_history = []
        self.max_history_turns = 6

        self.log_queue = None

    def set_log_queue(self, queue):
        self.log_queue = queue

    def verify_manual_path(self, path):
        path = path.strip(' \t\n\r"\'')
        path = path.replace('\u202a', '').replace('\u202c', '')
        path = os.path.normpath(path)

        if os.path.isfile(path) and path.lower().endswith('config.json'):
            path = os.path.dirname(path)

        if os.path.isfile(path) and path.lower().endswith('.gguf'):
            if "mmproj" in os.path.basename(path).lower():
                return False, "❌ 这是视觉权重文件 (mmproj)，请选择主模型文件，mmproj 会被自动配对。"
            model_dir = os.path.dirname(path)
            has_vl = any("mmproj" in f.lower() and f.lower().endswith(".gguf") for f in os.listdir(model_dir))
            vl_flag = "👁️VL " if has_vl else ""
            name = f"{vl_flag}GGUF: {os.path.basename(path)}"
            self.found_models_dict[name] = path
            return True, name

        elif os.path.isdir(path):
            if os.path.exists(os.path.join(path, "config.json")):
                try:
                    with open(os.path.join(path, "config.json"), "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    arch = cfg.get("architectures", [""])[0].lower()
                    mtype = cfg.get("model_type", "").lower()
                    vl_hints = ["vision", "vl", "llava", "qwenvl", "qwen2vl", "qwen3vl", "qwen3_5_vl", "qwen2_5_vl", "minicpm", "internvl", "idefics", "paligemma", "phi3v", "moondream"]
                    has_vl = any(h in arch + " " + mtype for h in vl_hints)
                except Exception:
                    has_vl = False
                vl_flag = "👁️VL " if has_vl else ""
                name = f"{vl_flag}PT: {os.path.basename(path)}"
                self.found_models_dict[name] = path
                return True, name

            for f in os.listdir(path):
                if f.lower().endswith('.gguf') and "mmproj" not in f.lower():
                    full_path = os.path.join(path, f)
                    has_vl = any("mmproj" in ff.lower() and ff.lower().endswith(".gguf") for ff in os.listdir(path))
                    vl_flag = "👁️VL " if has_vl else ""
                    name = f"{vl_flag}GGUF: {f}"
                    self.found_models_dict[name] = full_path
                    return True, name

        return False, f"❌ 路径无效或不包含可识别的模型文件: [{path}]"

    def scan_models(self, progress_callback=None):
        """全盘智能深度扫描，零配置自动发现所有模型"""
        self.found_models_dict = {}

        # 读取自定义热区
        extra_roots = []
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    extra_roots = cfg.get("model_search_paths", [])
            except: pass

        SKIP_DIRS = {
            "windows", "system32", "syswow64", "program files",
            "program files (x86)", "programdata", "appdata",
            "$recycle.bin", "system volume information",
            "node_modules", ".git", "__pycache__", "temp", "tmp",
            "cache", ".cache", "site-packages", "dist-packages"
        }

        vram_gb = 0
        if torch.cuda.is_available():
            try:
                vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            except Exception: pass

        def _tag(size_gb):
            if vram_gb == 0: return "💻CPU"
            if size_gb < vram_gb * 0.8: return "✅推荐"
            elif size_gb < vram_gb * 1.5: return "⚠️需量化"
            return "🔴过载"

        def _has_mmproj(directory):
            try: return any("mmproj" in f.lower() and f.lower().endswith(".gguf") for f in os.listdir(directory))
            except Exception: return False

        def _is_vl_pytorch(directory):
            try:
                with open(os.path.join(directory, "config.json"), "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                arch = cfg.get("architectures", [""])[0].lower()
                mtype = cfg.get("model_type", "").lower()
                combined = arch + " " + mtype
                vl_hints = ["vision", "vl", "llava", "qwenvl", "qwen2vl", "qwen3vl", "qwen3_5_vl", "qwen2_5_vl", "minicpm", "internvl", "idefics", "paligemma", "phi3v", "moondream", "florence", "smolvlm", "deepseek_vl"]
                return any(h in combined for h in vl_hints)
            except Exception: return False

        def _register_gguf(file_path):
            fname = os.path.basename(file_path)
            if "mmproj" in fname.lower(): return 
            try: size_gb = os.path.getsize(file_path) / (1024**3)
            except Exception: return
            model_dir = os.path.dirname(file_path)
            has_vl = _has_mmproj(model_dir)
            vl_flag = "👁️VL " if has_vl else ""
            key = f"[{_tag(size_gb)}] {vl_flag}GGUF: {fname}"
            if key not in self.found_models_dict:
                self.found_models_dict[key] = file_path
                if progress_callback: progress_callback(key)

        def _register_pt(dir_path):
            dname = os.path.basename(dir_path)
            try:
                size_gb = sum(os.path.getsize(os.path.join(dir_path, f)) for f in os.listdir(dir_path) if f.endswith((".bin", ".safetensors", ".pt"))) / (1024**3)
            except Exception: return
            has_vl = _is_vl_pytorch(dir_path)
            vl_flag = "👁️VL " if has_vl else ""
            key = f"[{_tag(size_gb)}] {vl_flag}PT: {dname}"
            if key not in self.found_models_dict:
                self.found_models_dict[key] = dir_path
                if progress_callback: progress_callback(key)

        def _walk_dir(root, max_depth=4):
            if not os.path.exists(root): return
            try:
                for dirpath, dirnames, filenames in os.walk(root):
                    depth = dirpath.replace(root, "").count(os.sep)
                    if depth >= max_depth:
                        dirnames.clear()
                        continue
                    dirnames[:] = [d for d in dirnames if d.lower() not in SKIP_DIRS and not d.startswith(".")]
                    if "config.json" in filenames:
                        _register_pt(dirpath)
                        dirnames.clear()  
                        continue
                    for f in filenames:
                        if f.lower().endswith(".gguf"):
                            _register_gguf(os.path.join(dirpath, f))
            except Exception: pass

        hot_zones = [os.path.join(os.getcwd(), "models"), os.getcwd()] + extra_roots
        MODEL_FOLDER_NAMES = ["models", "LLM", "llm", "AI", "ai_models", "gguf", "openclaw", "ollama", "lm-studio", "lm_studio", "text-generation-webui", "koboldcpp", "jan"]

        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        all_drives = []
        for i, letter in enumerate(string.ascii_uppercase):
            if bitmask & (1 << i):
                drive = f"{letter}:\\"
                if ctypes.windll.kernel32.GetDriveTypeW(drive) in [2, 3]:
                    all_drives.append(drive)
                    for name in MODEL_FOLDER_NAMES:
                        hot_zones.append(os.path.join(drive, name))

        for zone in hot_zones:
            _walk_dir(zone, max_depth=4)

        for drive in all_drives:
            depth = 2 if drive.upper().startswith("C") else 6
            _walk_dir(drive, max_depth=depth)

        return list(self.found_models_dict.keys())

    def _calculate_adaptive_quantization(self, model_path):
        if not torch.cuda.is_available():
            return None, "auto"

        total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        if total_vram_gb <= 4.5:
            return BitsAndBytesConfig(
                load_in_4bit=True, 
                bnb_4bit_quant_type="nf4", 
                bnb_4bit_compute_dtype=torch.float16, 
                bnb_4bit_use_double_quant=True,
                llm_int8_enable_fp32_cpu_offload=True 
            ), "auto"

        safe_vram_gb = total_vram_gb - 2.0
        model_size_bytes = sum(os.path.getsize(os.path.join(root, f)) for root, _, files in os.walk(model_path) for f in files if f.endswith(('.safetensors', '.bin', '.pt')))
        model_size_gb = model_size_bytes / (1024**3)

        if model_size_gb <= safe_vram_gb: return None, "auto"
        elif (model_size_gb * 0.55) <= safe_vram_gb: return BitsAndBytesConfig(load_in_8bit=True), "auto"
        else: return BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True), "auto"

    def load_selected_model(self, display_name):
        path = self.found_models_dict.get(display_name)
        if not path: return False
        try:
            if getattr(self, 'model_instance', None) is not None:
                del self.model_instance
                del self.processor
                self.model_instance = None
                self.processor = None
                self.conversation_history = [] 
                gc.collect()
                if torch.cuda.is_available(): torch.cuda.empty_cache() 
            
            if path.lower().endswith('.gguf'):
                self.engine_type = "gguf"
                self.has_vision = False
                self.vl_strategy = ""

                UNSUPPORTED_ARCH = {"qwen3vl", "qwen2vl", "minicpmv", "internvl"}
                try:
                    with open(path, "rb") as _f:
                        _f.seek(8)
                        raw_head = _f.read(512)
                    arch_hint = raw_head.decode("utf-8", errors="ignore").lower()
                    for bad_arch in UNSUPPORTED_ARCH:
                        if bad_arch in arch_hint:
                            handler_name = GGUF_VL_HANDLERS.get(bad_arch)
                            handler_available = False
                            if handler_name:
                                try:
                                    from llama_cpp import llama_chat_format as _lcf
                                    handler_available = hasattr(_lcf, handler_name)
                                except Exception: pass
                            if not handler_available:
                                msg = (f"⚠️ GGUF 架构 [{bad_arch}] 需要更新版本的 llama-cpp-python 支持。\n"
                                       f"💡 建议：pip install -U llama-cpp-python，或改用 PyTorch 引擎加载。")
                                print(msg)
                                if self.log_queue: self.log_queue.put(msg)
                                return False
                except Exception as _e: pass

                model_name_lower = os.path.basename(path).lower()
                model_dir = os.path.dirname(path)
                chat_handler, self.has_vision = _get_gguf_vl_handler(model_name_lower, model_dir)

                gpu_layers = -1 if torch.cuda.is_available() else 0
                kwargs = {
                    "model_path": path,
                    "n_gpu_layers": gpu_layers,
                    "n_ctx": 2048, # 🚨 恢复绝对安全的 2048
                    "verbose": False
                }
                if self.has_vision and chat_handler:
                    kwargs["chat_handler"] = chat_handler

                print(f"⚙️ 正在通过 GGUF 引擎加载... (视觉能力: {self.has_vision})")
                
                try:
                    self.model_instance = Llama(**kwargs)
                except Exception as e:
                    if self.has_vision:
                        print(f"⚠️ 视神经排异，降级到纯文本模式重试: {e}")
                        self.has_vision = False
                        kwargs.pop("chat_handler", None)
                        self.model_instance = Llama(**kwargs)
                    else:
                        raise e

            else:
                self.engine_type = "pytorch"
                self.has_vision = False
                self.vl_strategy = ""

                config_path = os.path.join(path, "config.json")
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                arch_name = config_data.get("architectures", [""])[0]
                model_type = config_data.get("model_type", "")

                try:
                    self.processor = AutoProcessor.from_pretrained(path, trust_remote_code=True)
                except Exception:
                    self.processor = AutoTokenizer.from_pretrained(path, trust_remote_code=True)

                self.vl_strategy = _detect_pytorch_vl_strategy(arch_name, model_type, self.processor)
                self.has_vision = bool(self.vl_strategy)

                if self.has_vision:
                    log_msg = f"👁️ 检测到 VL 架构: {arch_name}，图像策略: [{self.vl_strategy}]"
                    print(log_msg)
                    if self.log_queue: self.log_queue.put(log_msg)

                import transformers as _tf
                arch_lower = arch_name.lower()
                target_class = AutoModelForCausalLM

                if self.has_vision:
                    if arch_lower in VL_LOAD_PREFER_VISION2SEQ:
                        try:
                            from transformers import AutoModelForVision2Seq
                            target_class = AutoModelForVision2Seq
                        except ImportError: pass
                    elif arch_name and hasattr(_tf, arch_name):
                        target_class = getattr(_tf, arch_name)
                    else:
                        try:
                            from transformers import AutoModelForVision2Seq
                            target_class = AutoModelForVision2Seq
                        except ImportError: pass

                quantization_config, dev_map = self._calculate_adaptive_quantization(path)
                self.model_instance = target_class.from_pretrained(
                    path, device_map=dev_map, quantization_config=quantization_config, trust_remote_code=True
                )
            return True
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            print(f"❌ 加载崩溃详情: {error_msg}")
            if self.log_queue:
                self.log_queue.put(f"❌ 加载崩溃: {error_msg}")
            self.model_instance = None
            return False

    def ask(self, prompt, lang="zh-CN", frame=None, context="", apps_list=None):
        if not self.model_instance: 
            return "大脑未就绪。"
            
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        name = "小智" if "zh" in lang else "Tom"
        current_time = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

        # 构建已知程序列表
        apps_hint = ""
        if apps_list:
            top_apps = list(apps_list)[:30]  
            apps_hint = f"\n【已知可操控程序清单】（使用 MACRO 时目标名必须从此列表选取）：{', '.join(top_apps)}\n"

        # Skill 注入
        try:
            from skill_manager import skill_manager as _sm
            skill_ctx   = _sm.build_skill_context(prompt)
            skills_hint = _sm.build_skills_list_hint()
        except Exception:
            skill_ctx   = ""
            skills_hint = ""

        sys_msg = (
            f"你是{name}，一个强大的具身智能管家。当前时间是 {current_time}。\n"
            f"{apps_hint}"
            "【最高执行法则】（绝对遵守，不可组合）：\n"
            "1. 🚨如果用户要求写代码（如爬虫/脚本）并保存，【只能】输出：[CODE]\n"
            "2. 🚨打开软件并进行操作，必须输出宏指令，格式：[MACRO:软件名|动作序列]\n"
            "   - 基础动作：wait N（等待N秒）, press 键名, hotkey 键1 键2\n"
            "   - 输入文字：type 内容（支持中文）\n"
            "   - 点击屏幕文字（三层识别）：click_text 屏幕上的文字\n"
            "   - Win32原生控件点击（最稳定）：win_click 控件名\n"
            "   - 强制激活窗口：focus 窗口标题关键字\n"
            "   - 示例（打开trae并新建文件写爬虫）：[MACRO:trae|wait 3, hotkey ctrl n, wait 1, type import requests]\n"
            "   - 示例（打开微信发消息）：[MACRO:微信|wait 2, win_click 搜索, type 张三, press enter, type 你好, win_click 发送]\n"
            "3. 仅唤醒软件或打开网页：输出 [MACRO:软件名|wait 1]\n"
            "4. 搜索引擎搜索：输出 [SEARCH:关键词]\n"
            "5. 抓取网页：输出 [READ:网址]\n"
            "6. 每次回复【只能输出一条】指令，绝不废话！\n"
            "7. - 示例（打开C盘）：[MACRO:C:\\|wait 1]\n"
            "8. - 示例（打开项目文件夹）：[MACRO:D:\\Projects|wait 1]\n"
        )

        if skill_ctx:
            sys_msg += f"\n\n{skill_ctx}"
        elif skills_hint:
            sys_msg += f"\n\n{skills_hint}"

        self.conversation_history.append({"role": "user", "content": str(prompt)})

        is_code_task = "严禁输出Markdown" in context
        is_complex_action = any(k in prompt for k in ["宏", "macro", "打开并", "发送", "搜索并"])
        max_len = 4096 if is_code_task else (512 if is_complex_action else 256)
        
        pil_image = None
        base64_image = None

        if frame is not None and self.has_vision:
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb_frame = cv2.resize(rgb_frame, (512, 512))
                pil_image = Image.fromarray(rgb_frame)
                if self.engine_type == "gguf":
                    _, buffer = cv2.imencode('.jpg', rgb_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    base64_image = base64.b64encode(buffer).decode('utf-8')
            except Exception: pass

        try:
            raw_text = ""

            if self.engine_type == "gguf":
                messages = [{"role": "system", "content": sys_msg}]
                messages.extend(self.conversation_history[-(self.max_history_turns * 2 + 1):-1])

                if base64_image:
                    messages.append({"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                        {"type": "text", "text": prompt}
                    ]})
                else:
                    messages.append({"role": "user", "content": prompt})

                response = self.model_instance.create_chat_completion(
                    messages=messages, max_tokens=max_len, temperature=0.2
                )
                raw_text = response["choices"][0]["message"]["content"].strip()

            else:
                messages = [{"role": "system", "content": sys_msg}]
                messages.extend(self.conversation_history[-(self.max_history_turns * 2 + 1):-1])

                success_vlm = False

                if self.has_vision and pil_image and self.vl_strategy:
                    try:
                        if self.vl_strategy == "qwen2vl":
                            messages.append({"role": "user", "content": [
                                {"type": "image", "image": pil_image},
                                {"type": "text",  "text": prompt}
                            ]})
                            text = self.processor.apply_chat_template(
                                messages, tokenize=False, add_generation_prompt=True
                            )
                            if _qwen_process_vision_info:
                                image_inputs, video_inputs = _qwen_process_vision_info(messages)
                                model_inputs = self.processor(
                                    text=[text], images=image_inputs,
                                    videos=video_inputs, padding=True, return_tensors="pt"
                                ).to(device)
                            else:
                                model_inputs = self.processor(
                                    text=[text], images=[pil_image],
                                    padding=True, return_tensors="pt"
                                ).to(device)

                        elif self.vl_strategy == "idefics":
                            messages.append({"role": "user", "content": [
                                {"type": "image"},
                                {"type": "text", "text": prompt}
                            ]})
                            text = self.processor.apply_chat_template(messages, add_generation_prompt=True)
                            model_inputs = self.processor(text=text, images=[pil_image], return_tensors="pt").to(device)

                        else:
                            messages.append({"role": "user", "content": [
                                {"type": "image", "image": pil_image},
                                {"type": "text",  "text": prompt}
                            ]})
                            text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                            model_inputs = self.processor(text=[text], images=[pil_image], padding=True, return_tensors="pt").to(device)

                        generated_ids = self.model_instance.generate(**model_inputs, max_new_tokens=max_len)
                        generated_ids_trimmed = [out[len(inp):] for inp, out in zip(model_inputs.input_ids, generated_ids)]
                        raw_text = self.processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True)[0]
                        success_vlm = True

                    except Exception as vl_err:
                        print(f"⚠️ VL 推理失败 (策略:{self.vl_strategy})，降级到纯文本: {vl_err}")
                        success_vlm = False

                if not success_vlm:
                    # 🚨 原版神级修复：强制洗掉之前失败残留的图片 Dict
                    if messages and messages[-1]["role"] == "user":
                        messages[-1] = {"role": "user", "content": str(prompt)}
                    else:
                        messages.append({"role": "user", "content": str(prompt)})

                    tokenizer = getattr(self.processor, "tokenizer", self.processor)
                    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                    text += "<think>\n不需要思考，直接出答案。\n</think>\n"
                    model_inputs = tokenizer([text], return_tensors="pt").to(device)
                    generated_ids = self.model_instance.generate(
                        **model_inputs, max_new_tokens=max_len, pad_token_id=getattr(tokenizer, "eos_token_id", None)
                    )
                    generated_ids_trimmed = [out[len(inp):] for inp, out in zip(model_inputs.input_ids, generated_ids)]
                    raw_text = tokenizer.batch_decode(generated_ids_trimmed, skip_special_tokens=True)[0]

            if not raw_text:
                return "抱歉，刚刚走神了，能再说一遍吗？"

            res_text = re.sub(r'<\|.*?\|>', '', raw_text).strip()
            res_text = re.sub(r'[\U00010000-\U0010ffff]', '', res_text).strip()

            self.conversation_history.append({"role": "assistant", "content": res_text})
            return res_text

        except Exception as e:
            return f"思考链路异常: {e}"

    def clear_history(self):
        self.conversation_history = []

brain_manager = LocalModelManager()