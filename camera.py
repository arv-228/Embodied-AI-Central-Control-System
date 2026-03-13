import cv2
import threading
import time
import queue
from ultralytics import YOLO

class CameraStream:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        
        # 🚀 生产者-消费者队列，彻底分离画面采集与 AI 推理
        self.frame_queue = queue.Queue(maxsize=1) 
        
        # 🚨 回归你本地稳定存在的模型版本，防止找不到文件报错
        print("⏳ 正在加载 YOLO 骨骼追踪雷达...")
        self.model = YOLO('yolov8n-pose.pt') 
        
        self.dynamic_state = {
            "target_locked": False,
            "mouth_open": False,
            "gaze_center": (0, 0),
            "gesture": None
        }

    def start(self):
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW) 
        if not self.cap.isOpened():
            print("❌ 无法连接到摄像头！")
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        self.running = True
        threading.Thread(target=self._capture_thread, daemon=True).start()
        threading.Thread(target=self._inference_thread, daemon=True).start()
        print("📷 YOLO 骨骼雷达已上线 (全域锁定模式启动，双线程极速分离)")

    def _capture_thread(self):
        while self.running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1) 
                if not self.frame_queue.full():
                    self.frame_queue.put(frame)
                
                with self.lock:
                    if self.frame is None:
                        self.frame = frame
            else:
                time.sleep(0.01)

    def _inference_thread(self):
        while self.running:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                processed_frame = self._process_tracking(frame)
                with self.lock:
                    self.frame = processed_frame
            else:
                time.sleep(0.01)

    def _process_tracking(self, frame):
        results = self.model(frame, verbose=False, imgsz=320)
        self.dynamic_state["target_locked"] = False
        annotated_frame = frame.copy()
        
        if len(results) > 0 and results[0].keypoints is not None:
            keypoints = results[0].keypoints.xy.cpu().numpy() 
            if len(keypoints) > 0 and len(keypoints[0]) >= 5:
                self.dynamic_state["target_locked"] = True
                nose = keypoints[0][0]
                left_eye = keypoints[0][1]
                right_eye = keypoints[0][2]
                
                if left_eye[0] > 0 and right_eye[0] > 0:
                    gx = int((left_eye[0] + right_eye[0]) / 2)
                    gy = int((left_eye[1] + right_eye[1]) / 2)
                    self.dynamic_state["gaze_center"] = (gx, gy)

                if len(keypoints[0]) >= 11:
                    left_wrist = keypoints[0][9]
                    right_wrist = keypoints[0][10]
                    if (left_wrist[1] > 0 and left_wrist[1] < nose[1]) or (right_wrist[1] > 0 and right_wrist[1] < nose[1]):
                        self.dynamic_state["gesture"] = "HAND_UP"
                        cv2.putText(annotated_frame, "[GESTURE: HAND UP]", (int(nose[0]), int(nose[1]) - 50), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    else:
                        self.dynamic_state["gesture"] = None

            # 🚨 留空：注释掉 plot 即可实现只运算不画骨骼的“隐形雷达”，如果想看线条，去掉下面这行的注释符即可
            # annotated_frame = results[0].plot()

        return annotated_frame

    def get_frame(self):
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
        return None
        
    def get_dynamic_state(self):
        with self.lock:
            return self.dynamic_state.copy()

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        print("📷 YOLO 骨骼雷达已安全关闭")