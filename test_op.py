"""
Тест OpenPose напрямую
"""

import subprocess
import cv2
import tempfile
import os
import json

OPENPOSE_PATH = r"D:\openpose\openpose"
OPENPOSE_EXE = os.path.join(OPENPOSE_PATH, "bin", "OpenPoseDemo.exe")

# Захват с камеры
cap = cv2.VideoCapture(0)

print("📷 Нажмите 's' для анализа кадра, 'q' для выхода")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    cv2.imshow("Test", frame)
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('s'):
        print("\nАнализируем кадр...")
        
        # Сохраняем кадр
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, "frame.jpg")
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        cv2.imwrite(input_path, frame)
        print(f"Saved frame to {input_path}")
        
        # Запускаем OpenPose
        cmd = [
            OPENPOSE_EXE,
            "--image_dir", temp_dir,
            "--write_json", output_dir,
            "--display", "0",
            "--render_pose", "0",
            "--model_pose", "COCO",
            "--num_gpu", "0"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        print(f"Return code: {result.returncode}")
        
        # Ищем JSON
        json_files = []
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                if f.endswith('.json'):
                    json_files.append(os.path.join(root, f))
        
        if json_files:
            with open(json_files[0], 'r') as f:
                data = json.load(f)
                print(f"📄 JSON: {json.dumps(data, indent=2)[:500]}")
                
                if "people" in data and len(data["people"]) > 0:
                    print(f"Найдено людей: {len(data['people'])}")
                    keypoints = data["people"][0].get("pose_keypoints_2d", [])
                    visible = sum(1 for i in range(0, len(keypoints), 3) if keypoints[i+2] > 0.3)
                    print(f"Ключевых точек: {visible}")
                else:
                    print("Люди не обнаружены!")
        else:
            print("JSON файл не найден!")
            
        # Очистка
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()