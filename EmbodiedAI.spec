# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'], # 🚨 使用点号代表当前相对路径，干掉绝对路径！
    binaries=[],
    datas=[
        ('models', 'models'), # 确保本地模型文件夹被打包或映射
        ('apps_db.json', '.'), 
        ('yolov8n-pose.pt', '.')
    ],
    hiddenimports=[
        'torch', 'torchvision', 'torchaudio', 'transformers', 
        'pyautogui', 'pyperclip', 'cv2', 'pynvml', 'PyQt5',
        'llama_cpp' # 确保 C++ 引擎被强制引入
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EmbodiedAI_Central',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, # 如果不想看黑框命令行，可以把这里改成 False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico' # 如果你有图标，可以放个 ico 文件在目录里
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EmbodiedAI_Central',
)