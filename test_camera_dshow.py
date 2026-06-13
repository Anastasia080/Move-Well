"""
Тест камеры с использованием DirectShow
"""

import cv2

print("Проверка камеры с DirectShow...")

# Используем DShow бэкенд
for camera_idx in [0, 1]:
    cap = cv2.VideoCapture(camera_idx, cv2.CAP_DSHOW)  # Явно указываем DShow
    if cap.isOpened():
        # Устанавливаем параметры
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        ret, frame = cap.read()
        if ret and frame is not None:
            print(f"Камера {camera_idx} работает!")
            cv2.imwrite(f"camera_{camera_idx}_test.jpg", frame)
            print(f"Сохранен кадр camera_{camera_idx}_test.jpg")
            
            # Показываем кадр
            cv2.imshow(f"Camera {camera_idx}", frame)
            cv2.waitKey(1000)
            cv2.destroyAllWindows()
        else:
            print(f"Камера {camera_idx} открыта, но кадр пустой")
        cap.release()
    else:
        print(f"Камера {camera_idx} не найдена")

print("\nЕсли камера не работает, попробуйте:")
print("   1. Закрыть другие приложения с камерой (Zoom, Skype, браузер)")
print("   2. Перезагрузить компьютер")
print("   3. Проверить драйверы камеры")