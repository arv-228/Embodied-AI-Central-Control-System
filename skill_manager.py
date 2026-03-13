"""
skill_manager.py  —  EmbodiedAI 本地 Skill 系统

用法和模型扫描完全一样：
  - 用户把 .skill 文件或 skill 文件夹放进任意位置
  - 系统自动全盘扫描发现、加载、注入到 system prompt
  - 对话时根据意图自动匹配最合适的 skill

Skill 格式（两种都支持）：
  ① 单文件：  my_skill.skill       ← zip 包，内含 SKILL.md
  ② 文件夹：  my_skill/SKILL.md    ← 展开的 skill 目录

SKILL.md 必须有 YAML 前置元数据：
  ---
  name: 我的技能
  description: 当用户需要...时使用
  ---
  （技能正文指令）
"""

import os
import sys
import json
import re
import string
import zipfile
import ctypes
import threading
from pathlib import Path
from typing import Optional


# ── Skill 数据结构 ──────────────────────────────────────────────────────────────
class Skill:
    def __init__(self, name: str, description: str, body: str,
                 source_path: str, source_type: str):
        self.name        = name          # YAML frontmatter 里的 name
        self.description = description   # YAML frontmatter 里的 description
        self.body        = body          # SKILL.md 正文（去掉 frontmatter）
        self.source_path = source_path   # 原始文件/文件夹路径
        self.source_type = source_type   # "file"(.skill zip) 或 "folder"

    @property
    def display_name(self) -> str:
        """下拉框/日志显示名"""
        icon = "📦" if self.source_type == "file" else "📁"
        return f"{icon} {self.name}"

    def __repr__(self):
        return f"<Skill name={self.name!r} from={self.source_path!r}>"


# ── 解析工具 ─────────────────────────────────────────────────────────────────────
def _parse_skill_md(content: str, source_path: str) -> Optional[Skill]:
    """解析 SKILL.md 内容，提取 frontmatter 和正文"""
    content = content.strip()

    # 必须以 --- 开头才有 frontmatter
    if not content.startswith("---"):
        # 没有 frontmatter：用文件名作 name，全文作 description+body
        fname = Path(source_path).stem
        return None  # 强制要求有 frontmatter，跳过无效文件

    # 找结束 ---
    end = content.find("\n---", 3)
    if end == -1:
        return None

    frontmatter = content[3:end].strip()
    body = content[end + 4:].strip()

    # 解析 frontmatter（简单 key: value，不依赖 yaml 库）
    meta = {}
    for line in frontmatter.splitlines():
        line = line.strip()
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()

    name = meta.get("name", "").strip()
    description = meta.get("description", "").strip()

    if not name or not description:
        return None

    # 判断 source_type
    p = Path(source_path)
    src_type = "file" if p.suffix.lower() == ".skill" else "folder"

    return Skill(
        name=name,
        description=description,
        body=body,
        source_path=source_path,
        source_type=src_type,
    )


def _load_from_zip(skill_path: str) -> Optional[Skill]:
    """从 .skill（zip）文件加载"""
    try:
        with zipfile.ZipFile(skill_path, "r") as zf:
            # 找 SKILL.md（可能在子目录里）
            candidates = [n for n in zf.namelist()
                          if n.endswith("SKILL.md") and not n.startswith("__")]
            if not candidates:
                return None
            # 优先根目录
            target = next((c for c in candidates if "/" not in c.strip("/")), candidates[0])
            content = zf.read(target).decode("utf-8", errors="replace")
            return _parse_skill_md(content, skill_path)
    except Exception:
        return None


def _load_from_folder(folder_path: str) -> Optional[Skill]:
    """从展开的 skill 文件夹加载"""
    skill_md = os.path.join(folder_path, "SKILL.md")
    if not os.path.isfile(skill_md):
        return None
    try:
        with open(skill_md, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return _parse_skill_md(content, folder_path)
    except Exception:
        return None


# ── 主管理器 ─────────────────────────────────────────────────────────────────────
class SkillManager:
    """
    全盘扫描 .skill 文件和 skill 文件夹，提供：
      - 自动匹配当前意图的 skill
      - 注入 system prompt 的接口
      - GUI 展示用的列表
    """

    # 扫描时跳过这些目录（避免深入系统目录拖慢速度）
    SKIP_DIRS = {
        "windows", "program files", "program files (x86)",
        "$recycle.bin", "system volume information",
        "programdata", "recovery", "perflogs",
        "__pycache__", "node_modules", ".git",
    }

    # 扫描优先查找的子目录名（会在每个磁盘根目录下查）
    PRIORITY_SUBDIRS = ["skills", "skill", "embodied_skills", "my_skills", "ai_skills"]

    def __init__(self, logger_func=None):
        self._skills: dict[str, Skill] = {}   # display_name → Skill
        self._lock = threading.Lock()
        self._log = logger_func or print
        self._scan_done = False

    # ── 扫描 ────────────────────────────────────────────────────────────────────
    def scan_skills(self, callback=None) -> list[str]:
        """
        全盘扫描，返回 display_name 列表。
        callback(display_names) 在扫描结束时被调用（用于更新 GUI）。
        建议在后台线程调用。
        """
        found: dict[str, Skill] = {}

        roots = self._get_scan_roots()
        self._log("🔍 [Skill] 开始扫描技能库...")

        for root in roots:
            if not os.path.exists(root):
                continue
            self._scan_dir(root, found, depth=0, max_depth=6)

        with self._lock:
            self._skills = found

        self._scan_done = True
        names = list(found.keys())
        self._log(f"✅ [Skill] 扫描完成，发现 {len(names)} 个技能：{[s.name for s in found.values()]}")

        if callback:
            callback(names)
        return names

    def _get_scan_roots(self) -> list[str]:
        """生成扫描根目录列表：exe 同级 > 每个磁盘的 skills/ > 磁盘根"""
        roots = []

        # 1. exe / 脚本同级的 skills/ 目录（最高优先）
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.getcwd()

        for sub in self.PRIORITY_SUBDIRS:
            p = os.path.join(base, sub)
            if os.path.isdir(p):
                roots.insert(0, p)

        # 2. 所有本地/可移动磁盘
        try:
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for i, letter in enumerate(string.ascii_uppercase):
                if bitmask & (1 << i):
                    drive = f"{letter}:\\"
                    dtype = ctypes.windll.kernel32.GetDriveTypeW(drive)
                    if dtype in (2, 3):  # 可移动 / 固定
                        roots.append(drive)
                        for sub in self.PRIORITY_SUBDIRS:
                            p = os.path.join(drive, sub)
                            roots.append(p)
        except Exception:
            pass

        return list(dict.fromkeys(roots))  # 去重保序

    def _scan_dir(self, path: str, found: dict, depth: int, max_depth: int):
        if depth > max_depth:
            return
        try:
            entries = os.listdir(path)
        except PermissionError:
            return
        except Exception:
            return

        for entry in entries:
            full = os.path.join(path, entry)

            # ── .skill 文件 ──
            if entry.lower().endswith(".skill") and os.path.isfile(full):
                skill = _load_from_zip(full)
                if skill:
                    self._register(skill, found)
                continue

            # ── SKILL.md 所在文件夹 ──
            if os.path.isdir(full):
                lower = entry.lower()
                if lower in self.SKIP_DIRS:
                    continue
                if os.path.isfile(os.path.join(full, "SKILL.md")):
                    skill = _load_from_folder(full)
                    if skill:
                        self._register(skill, found)
                    # 仍然递归，因为可能有嵌套 skill
                self._scan_dir(full, found, depth + 1, max_depth)

    def _register(self, skill: Skill, target: dict):
        key = skill.display_name
        # 名称冲突：加后缀区分
        if key in target:
            key = f"{key} [{Path(skill.source_path).stem}]"
        target[key] = skill
        self._log(f"  📌 [Skill] 已收录: {skill.name}  ({skill.source_path})")

    # ── 查询 / 匹配 ─────────────────────────────────────────────────────────────
    def get_all(self) -> dict[str, Skill]:
        with self._lock:
            return dict(self._skills)

    def get_by_display_name(self, display_name: str) -> Optional[Skill]:
        with self._lock:
            return self._skills.get(display_name)

    def match_for_prompt(self, prompt: str, top_k: int = 2) -> list[Skill]:
        """
        根据用户输入自动匹配最相关的 skill。
        算法：关键词覆盖率打分（不依赖任何 ML 库）。
        """
        with self._lock:
            skills = list(self._skills.values())

        if not skills:
            return []

        prompt_lower = prompt.lower()
        # 分词（中英文混合粗分）
        tokens = set(re.findall(r'[\w\u4e00-\u9fff]+', prompt_lower))

        scored = []
        for skill in skills:
            target = (skill.name + " " + skill.description).lower()
            target_tokens = set(re.findall(r'[\w\u4e00-\u9fff]+', target))
            overlap = tokens & target_tokens
            if not overlap:
                continue
            # 覆盖率：命中词 / max(prompt词, description词)
            score = len(overlap) / max(len(tokens), len(target_tokens), 1)
            scored.append((score, skill))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:top_k] if _ > 0.05]

    # ── 注入 system prompt ───────────────────────────────────────────────────────
    def build_skill_context(self, prompt: str) -> str:
        """
        自动匹配并拼接最多 2 个 skill 的指令正文，
        用于注入到 ask() 的 sys_msg 里。
        没有匹配到时返回空字符串。
        """
        matched = self.match_for_prompt(prompt)
        if not matched:
            return ""

        parts = []
        for skill in matched:
            parts.append(
                f"\n【技能 · {skill.name}】\n"
                f"{skill.body}\n"
                "【技能结束】"
            )
        return "\n".join(parts)

    def build_skills_list_hint(self) -> str:
        """
        生成已加载 skill 清单，注入 system prompt 让模型知道有哪些技能可用。
        """
        with self._lock:
            skills = list(self._skills.values())
        if not skills:
            return ""
        lines = ["【已加载技能清单】"]
        for skill in skills:
            lines.append(f"  · {skill.name}：{skill.description[:60]}{'…' if len(skill.description)>60 else ''}")
        return "\n".join(lines)

    # ── 手动加载（用户拖入） ──────────────────────────────────────────────────────
    def load_from_path(self, path: str) -> Optional[str]:
        """
        手动加载单个 .skill 文件或 skill 文件夹。
        成功返回 display_name，失败返回 None。
        """
        p = Path(path)
        if p.suffix.lower() == ".skill" and p.is_file():
            skill = _load_from_zip(path)
        elif p.is_dir() and (p / "SKILL.md").exists():
            skill = _load_from_folder(path)
        else:
            self._log(f"⚠️ [Skill] 无法加载: {path}")
            return None

        if skill is None:
            self._log(f"⚠️ [Skill] 解析失败（请检查 SKILL.md 格式）: {path}")
            return None

        with self._lock:
            key = skill.display_name
            if key in self._skills:
                key = f"{key} [{p.stem}]"
            self._skills[key] = skill

        self._log(f"✅ [Skill] 手动加载成功: {skill.name}")
        return key

    def remove(self, display_name: str) -> bool:
        with self._lock:
            if display_name in self._skills:
                del self._skills[display_name]
                return True
        return False


# ── 全局单例 ─────────────────────────────────────────────────────────────────────
skill_manager = SkillManager()