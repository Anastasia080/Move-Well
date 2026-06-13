"""
Прямой тест OpenPose из Python (для версии без --image)
"""

import subprocess
import cv2
import numpy as np
import tempfile
import os
import json
import shutil

# Путь к OpenPose
OPENPOSE_PATH = r"D:\openpose\openpose"
OPENPOSE_EXE = os.path.join(OPENPOSE_PATH, "bin", "OpenPoseDemo.exe")

# Захват с камеры
cap = cv2.VideoCapture(0)

print("📷 Нажмите 's' для анализа кадра, 'q' для выхода")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Показываем кадр
    cv2.imshow("Test", frame)
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('s'):
        print("🔍 Анализируем кадр...")
        
        # Создаем временную папку
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, "frame.jpg")
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        cv2.imwrite(input_path, frame)
        print(f"📸 Сохранено: {input_path}")
        
        # Запускаем OpenPose через image_dir
        cmd = [
            OPENPOSE_EXE,
            "--image_dir", temp_dir,  # папка с изображениями
            "--write_json", output_dir,  # куда сохранять JSON
            "--display", "0",
            "--render_pose", "0",
            "--model_pose", "BODY_25",
            "--num_gpu", "0"
        ]
        
        print(f"🚀 Запуск: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Stdout: {result.stdout[:500]}")
        if result.stderr:
            print(f"Stderr: {result.stderr[:500]}")
        
        # Ищем JSON результат
        json_files = []
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                if f.endswith('.json'):
                    json_files.append(os.path.join(root, f))
        
        if json_files:
            with open(json_files[0], 'r') as f:
                data = json.load(f)
                people_count = len(data.get("people", []))
                print(f"👥 Найдено людей в кадре: {people_count}")
                
                if people_count > 0:
                    keypoints = data["people"][0].get("pose_keypoints_2d", [])
                    visible = sum(1 for i in range(0, len(keypoints), 3) if keypoints[i+2] > 0.3)
                    print(f"✅ Обнаружено ключевых точек: {visible}")
                else:
                    print("❌ Люди не обнаружены. Попробуйте:")
                    print("   1. Встаньте в полный рост в кадр")
                    print("   2. Убедитесь, что освещение хорошее")
                    print("   3. Попробуйте модель COCO вместо BODY_25")
        else:
            print("❌ JSON файл не найден")
        
        # Чистим
        shutil.rmtree(temp_dir)
        
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()