import psutil, torch, time, gc

class ResourceManager:
    def __init__(self):
        self.last_check = 0
        psutil.cpu_percent(interval=None)

    def monitor_and_adjust(self):
        now = time.time()
        if now - self.last_check < 4: return 
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        if cpu > 85: print(f"⚠️ 核心过载: {cpu}%")
        if ram > 85:
            gc.collect()
            if torch.cuda.is_available(): torch.cuda.empty_cache()
        self.last_check = now