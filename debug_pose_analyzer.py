"""
Отладочная версия PoseAnalyzer с улучшенными параметрами
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

class PoseAnalyzer:
    def __init__(self, openpose_path: str = r"D:\openpose\openpose", confidence_threshold: float = 0.1):
        self.openpose_path = openpose_path
        self.openpose_exe = os.path.join(openpose_path, "bin", "OpenPoseDemo.exe")
        self.confidence_threshold = confidence_threshold
        
        print(f"🔍 DEBUG: OpenPose path: {self.openpose_path}")
        print(f"🔍 DEBUG: OpenPose exe: {self.openpose_exe}")
        print(f"🔍 DEBUG: Exists: {os.path.exists(self.openpose_exe)}")
        
        if not os.path.exists(self.openpose_exe):
            raise FileNotFoundError(f"OpenPose not found at {self.openpose_exe}")
    
    def analyze_image(self, image: np.ndarray) -> Tuple[List[Optional[Joint]], np.ndarray]:
        print(f"🔍 DEBUG: analyze_image called with shape: {image.shape}")
        
        # Сохраняем кадр для отладки
        debug_frame_path = "debug_current_frame.jpg"
        cv2.imwrite(debug_frame_path, image)
        print(f"🔍 DEBUG: Saved debug frame to {debug_frame_path}")
        
        # Создаем временную папку
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, "frame.jpg")
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        cv2.imwrite(input_path, image)
        print(f"🔍 DEBUG: Saved to temp: {input_path}")
        
        try:
            # Улучшенные параметры OpenPose
            cmd = [
                self.openpose_exe,
                "--image_dir", temp_dir,
                "--write_json", output_dir,
                "--display", "0",
                "--render_pose", "1",
                "--write_images", output_dir,
                "--model_pose", "COCO",
                "--num_gpu", "0",
                "--face", "0",           # Отключаем лицо для скорости
                "--hand", "0",           # Отключаем руки
                "--render_threshold", "0.05",  # Низкий порог для отображения
                "--net_resolution", "-1x368",  # Стандартное разрешение
                "--scale_number", "1",
                "--scale_gap", "0.25"
            ]
            
            print(f"🔍 DEBUG: Running command...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            print(f"🔍 DEBUG: Return code: {result.returncode}")
            print(f"🔍 DEBUG: Stdout last 500 chars: {result.stdout[-500:] if result.stdout else 'empty'}")
            
            # Проверяем выходные файлы
            print(f"🔍 DEBUG: Output dir contents: {os.listdir(output_dir) if os.path.exists(output_dir) else 'not exists'}")
            
            # Ищем JSON и рендеренные изображения
            json_files = []
            rendered_files = []
            for root, dirs, files in os.walk(output_dir):
                for f in files:
                    if f.endswith('.json'):
                        json_files.append(os.path.join(root, f))
                    if f.endswith('_rendered.jpg'):
                        rendered_files.append(os.path.join(root, f))
            
            print(f"🔍 DEBUG: JSON files: {len(json_files)}")
            print(f"🔍 DEBUG: Rendered files: {len(rendered_files)}")
            
            # Если есть рендеренное изображение, сохраняем его
            if rendered_files:
                rendered_img = cv2.imread(rendered_files[0])
                cv2.imwrite("debug_rendered_output.jpg", rendered_img)
                print("🔍 DEBUG: Saved rendered output to debug_rendered_output.jpg")
            
            # Парсим JSON
            joints = self._parse_openpose_output(output_dir)
            
            visible_count = sum(1 for j in joints if j is not None)
            print(f"🔍 DEBUG: Visible joints: {visible_count}")
            
            skeleton_image = self.draw_skeleton(image, joints)
            return joints, skeleton_image
            
        except subprocess.TimeoutExpired:
            print("❌ DEBUG: OpenPose timeout")
            return [None] * 18, image
        except Exception as e:
            print(f"❌ DEBUG: OpenPose error: {e}")
            import traceback
            traceback.print_exc()
            return [None] * 18, image
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _parse_openpose_output(self, output_dir: str) -> List[Optional[Joint]]:
        joints = [None] * 18
        
        try:
            json_files = []
            for root, dirs, files in os.walk(output_dir):
                for f in files:
                    if f.endswith('.json'):
                        json_files.append(os.path.join(root, f))
            
            if not json_files:
                print(f"🔍 DEBUG: No JSON files found in {output_dir}")
                return joints
            
            with open(json_files[0], 'r') as f:
                data = json.load(f)
                print(f"🔍 DEBUG: People count: {len(data.get('people', []))}")
            
            if "people" in data and len(data["people"]) > 0:
                person = data["people"][0]
                if "pose_keypoints_2d" in person:
                    keypoints = person["pose_keypoints_2d"]
                    for i in range(min(len(keypoints) // 3, 18)):
                        x = keypoints[i*3]
                        y = keypoints[i*3+1]
                        conf = keypoints[i*3+2]
                        if conf > self.confidence_threshold:
                            joints[i] = Joint(
                                x=x, y=y,
                                confidence=conf,
                                name=f"joint_{i}"
                            )
                            print(f"🔍 DEBUG: Joint {i}: ({x}, {y}) conf={conf:.2f}")
        except Exception as e:
            print(f"❌ DEBUG: Parse error: {e}")
        
        return joints
    
    def draw_skeleton(self, image: np.ndarray, joints: List[Optional[Joint]]) -> np.ndarray:
        img = image.copy()
        h, w = img.shape[:2]
        
        connections = [
            (1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7),
            (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13)
        ]
        
        for start, end in connections:
            if start < len(joints) and end < len(joints):
                j1, j2 = joints[start], joints[end]
                if j1 and j2:
                    x1, y1 = int(j1.x), int(j1.y)
                    x2, y2 = int(j2.x), int(j2.y)
                    if 0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h:
                        cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        for joint in joints:
            if joint:
                x, y = int(joint.x), int(joint.y)
                if 0 <= x < w and 0 <= y < h:
                    cv2.circle(img, (x, y), 4, (0, 0, 255), -1)
        
        return img


# Тест напрямую
if __name__ == "__main__":
    print("=" * 50)
    print("DEBUG: Testing PoseAnalyzer directly")
    print("=" * 50)
    
    # Инициализация
    analyzer = PoseAnalyzer()
    
    # Захват с камеры
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("❌ Camera not found!")
        exit()
    
    # Улучшаем качество кадра
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 150)
    
    print("✅ Camera opened. Press 's' to analyze, 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        cv2.imshow("Debug - Press 's'", frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('s'):
            print("\n" + "=" * 50)
            joints, skeleton = analyzer.analyze_image(frame)
            
            visible = sum(1 for j in joints if j)
            print(f"📊 RESULT: {visible} joints detected")
            
            if visible > 5:
                print("🎉 SUCCESS! Skeleton detected!")
                cv2.imshow("Skeleton", skeleton)
                cv2.waitKey(2000)
            else:
                print("❌ No skeleton detected!")
                print("💡 Try:")
                print("   1. Stand up so your whole body is visible")
                print("   2. Ensure good lighting")
                print("   3. Wear contrasting clothes")
            
            print("=" * 50)
            
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()