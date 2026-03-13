import sys, traceback
sys.path.insert(0, '.')
mods = [
    'gui', 'resource_manager', 'camera', 'voice', 'tts',
    'browser', 'permissions', 'log_manager', 'commands',
    'network', 'page_parser', 'code_detector', 'automation',
    'command_learning', 'ai_generator', 'model_config',
    'model_selector', 'ai_training_guide', 'embodied_ai_model'
]
for m in mods:
    try:
        __import__(m)
        print(f'OK  {m}')
    except Exception as e:
        print(f'FAIL {m}: {type(e).__name__}: {e}')
        traceback.print_exc()
        break

input("按回车退出")