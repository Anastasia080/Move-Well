import cv2
import os

# ПРАВИЛЬНЫЕ пути (с папкой openpose)
proto_path = r"C:\Users\танюшка\Desktop\movewell-backend\openpose\models\pose\coco\pose_deploy_linevec.prototxt"
weights_path = r"C:\Users\танюшка\Desktop\movewell-backend\openpose\models\pose\coco\pose_iter_440000.caffemodel"

print(f"Proto exists: {os.path.exists(proto_path)}")
print(f"Weights exists: {os.path.exists(weights_path)}")

try:
    print("Загрузка OpenPose...")
    net = cv2.dnn.readNetFromCaffe(proto_path, weights_path)
    print("OpenPose загружен успешно!")
except Exception as e:
    print(f"Ошибка: {e}")