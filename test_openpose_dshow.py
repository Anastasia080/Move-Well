"""
Тест OpenPose с камерой через OpenCV + DirectShow
"""

import subprocess
import cv2
import tempfile
import os
import json
import shutil

OPENPOSE_PATH = r"D:\openpose\openpose"
OPENPOSE_EXE = os.path.join(OPENPOSE_PATH, "bin", "OpenPoseDemo.exe")

if not os.path.exists(OPENPOSE_EXE):
    print(f"OpenPose не найден: {OPENPOSE_EXE}")
    exit()

print(f"OpenPose найден")

# Захват камеры через DirectShow
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Ключевой момент!

if not cap.isOpened():
    print("Камера 0 не найдена, пробуем камеру 1")
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Камера не найдена!")
    exit()

# Настройки камеры
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

print("Камера работает!")
print("Нажмите 's' для анализа кадра, 'q' для выхода")

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("Пустой кадр, пробуем снова...")
        continue
    
    cv2.imshow("Test - Press 's' to analyze, 'q' to quit", frame)
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('s'):
        frame_count += 1
        print(f"\nАнализируем кадр #{frame_count}...")
        
        # Сохраняем кадр
        temp_dir = tempfile.mkdtemp()
        input_path = os.path.join(temp_dir, "frame.jpg")
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        cv2.imwrite(input_path, frame)
        print(f"Сохранен: {input_path}")
        
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
        
        print(f"Запуск OpenPose...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        print(f"Return code: {result.returncode}")
        
        if result.stderr:
            print(f"Stderr: {result.stderr[:300]}")
        
        # Ищем JSON
        json_files = []
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                if f.endswith('.json'):
                    json_files.append(os.path.join(root, f))
        
        if json_files:
            with open(json_files[0], 'r') as f:
                data = json.load(f)
                people_count = len(data.get("people", []))
                print(f"Найдено людей: {people_count}")
                
                if people_count > 0:
                    keypoints = data["people"][0].get("pose_keypoints_2d", [])
                    visible = sum(1 for i in range(0, len(keypoints), 3) if keypoints[i+2] > 0.3)
                    print(f"Обнаружено ключевых точек: {visible}")
                    
                    if visible > 5:
                        print("Успех! Скелет обнаружен!")
                    else:
                        print("Мало точек. Попробуйте:")
                        print("   - Встать в полный рост")
                        print("   - Улучшить освещение")
                        print("   - Надеть контрастную одежду")
                else:
                    print("Люди не обнаружены!")
        else:
            print("JSON файл не найден!")
            
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("\nТест завершен")