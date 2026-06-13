"""
Прямая интеграция OpenPose в проект
"""

import subprocess
import json
import cv2
import numpy as np
import os
import tempfile
import shutil
from typing import List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class Joint:
    x: float
    y: float
    confidence: float
    name: str

class OpenPoseIntegration:
    def __init__(self, openpose_path: str = r"D:\openpose\openpose"):
        self.openpose_path = openpose_path
        self.openpose_exe = os.path.join(openpose_path, "bin", "OpenPoseDemo.exe")
        
        if not os.path.exists(self.openpose_exe):
            raise FileNotFoundError(f"OpenPose not found: {self.openpose_exe}")
        
        print(f"✅ OpenPose found: {self.openpose_exe}")
    
    def process_frame(self, frame: np.ndarray) -> Tuple[List[Optional[Joint]], np.ndarray]:
        # Сохраняем кадр
        temp_dir = tempfile.mkdtemp()
        img_path = os.path.join(temp_dir, "test.jpg")
        cv2.imwrite(img_path, frame)
        
        # ТОЧНО ТАКАЯ ЖЕ КОМАНДА КАК ВРУЧНУЮ
        cmd = [
            self.openpose_exe,
            "--image_dir", temp_dir,
            "--write_json", temp_dir,
            "--write_images", temp_dir,
            "--model_pose", "COCO",
            "--num_gpu", "0"
        ]
        
        print(f"CMD: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        print(f"Return code: {result.returncode}")
        print(f"STDERR: {result.stderr[:200]}")
        
        # Ищем результат
        json_file = None
        rendered_file = None
        
        for f in os.listdir(temp_dir):
            if f.endswith('.json'):
                json_file = os.path.join(temp_dir, f)
                print(f"Found JSON: {f}")
            if f.endswith('_rendered.jpg') or f.endswith('_rendered.png'):
                rendered_file = os.path.join(temp_dir, f)
                print(f"Found rendered: {f}")
        
        # Парсим JSON
        joints = [None] * 18
        if json_file:
            with open(json_file, 'r') as f:
                data = json.load(f)
                print(f"People in frame: {len(data.get('people', []))}")
                
                if data.get("people") and len(data["people"]) > 0:
                    keypoints = data["people"][0].get("pose_keypoints_2d", [])
                    for i in range(18):
                        if keypoints[i*3+2] > 0.1:
                            joints[i] = Joint(
                                x=keypoints[i*3],
                                y=keypoints[i*3+1],
                                confidence=keypoints[i*3+2],
                                name=f"joint_{i}"
                            )
        
        # Загружаем изображение со скелетом
        skeleton = cv2.imread(rendered_file) if rendered_file else frame
        
        # Очистка
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        visible = sum(1 for j in joints if j)
        print(f"Visible joints: {visible}")
        
        return joints, skeleton


# Тест
if __name__ == "__main__":
    print("Тест OpenPose интеграции")
    openpose = OpenPoseIntegration()
    
    # Захват с камеры
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("Нажмите 's' для обработки, 'q' для выхода")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        cv2.imshow("Camera", frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('s'):
            print("\n" + "="*50)
            joints, skeleton = openpose.process_frame(frame)
            visible = sum(1 for j in joints if j)
            
            if visible > 5:
                print(f"✅ УСПЕХ! Обнаружено {visible} точек!")
                cv2.imshow("Skeleton", skeleton)
                cv2.waitKey(2000)
            else:
                print(f"❌ Обнаружено только {visible} точек")
            print("="*50 + "\n")
            
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()