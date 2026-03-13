import os
from permissions import get_machine_signature

class NetworkAccess:
    def __init__(self):
        # 默认保持拦截状态，防患于未然
        self.is_allowed = False

    def request_permission(self):
        """
        🚀 终极改造：彻底废除恶心的二次弹窗！
        既然用户在开机前的主 GUI 权限界面已经同意过了，
        这里直接静默校验底层的硬件指纹授权文件。
        """
        try:
            # 抓取当前机器的设备指纹
            sig = get_machine_signature()
            
            # 校验全局授权文件
            if os.path.exists("permission_agreed.dat"):
                with open("permission_agreed.dat", "r") as f:
                    if f.read().strip() == sig:
                        # 指纹吻合，静默放行，绝不打扰用户！
                        self.is_allowed = True
                        return
        except Exception as e:
            print(f"⚠️ 权限指纹校验异常: {e}")
        
        # 兜底拦截：如果文件不存在或指纹对不上（被盗用），坚决拦截网络！
        self.is_allowed = False
        print("🚫 网络请求被底层拦截：未检测到合法的全局设备授权指纹。")