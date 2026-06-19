"""
OpenPose Processor - управляет процессом OpenPose в реальном времени
"""

import subprocess
import json
import cv2
import numpy as np
import os
import tempfile
import shutil
import threading
import queue
import time
from typing import List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class Joint:
    x: float
    y: float
    confidence: float
    name: str


class OpenPoseProcessor:
    """
    Процессор OpenPose для реального времени.
    Запускает OpenPose как отдельный процесс и читает его JSON вывод.
    """
    
    def __init__(self, openpose_path: str, confidence_threshold: float = 0.3):
        """
        Инициализация процессора
        
        Args:
            openpose_path: Путь к папке OpenPose (где лежит bin/OpenPoseDemo.exe)
            confidence_threshold: Порог уверенности для ключевых точек (0-1)
        """
        self.openpose_exe = os.path.join(openpose_path, "bin", "OpenPoseDemo.exe")
        self.confidence_threshold = confidence_threshold
        self.process = None
        self.running = False
        self.frame_queue = queue.Queue(maxsize=5)
        self.result_queue = queue.Queue(maxsize=5)
        self.input_dir = None
        self.output_dir = None
        
        # Проверяем существование OpenPose
        if not os.path.exists(self.openpose_exe):
            raise FileNotFoundError(f"OpenPose not found at {self.openpose_exe}")
        
        print(f"OpenPoseProcessor initialized")
        print(f"   Executable: {self.openpose_exe}")
    
    def start(self):
        """Запуск OpenPose процесса"""
        if self.running:
            print("OpenPose already running")
            return
        
        # Создаем временные папки
        self.input_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()
        
        print(f"Input dir: {self.input_dir}")
        print(f"Output dir: {self.output_dir}")
        
        # Команда запуска OpenPose
        cmd = [
            self.openpose_exe,
            "--image_dir", self.input_dir,
            "--write_json", self.output_dir,
            "--display", "0",
            "--render_pose", "0",
            "--model_pose", "COCO",
            "--num_gpu", "0"
        ]
        
        print(f"Starting OpenPose with command: {' '.join(cmd)}")
        
        # Запускаем процесс
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.running = True
        
        # Запускаем поток для чтения результатов
        self.read_thread = threading.Thread(target=self._read_results, daemon=True)
        self.read_thread.start()
        
        print("OpenPose processor started")
    
    def send_frame(self, frame: np.ndarray):
        """Отправка кадра на обработку"""
        if not self.running:
            print("Processor not running, call start() first")
            return
        
        try:
            # Сохраняем кадр во временную папку
            frame_path = os.path.join(self.input_dir, f"frame_{int(time.time()*1000)}.jpg")
            cv2.imwrite(frame_path, frame)
            self.frame_queue.put(frame_path, block=False)
        except queue.Full:
            pass
        except Exception as e:
            print(f"Error sending frame: {e}")
    
    def get_result(self, timeout: float = 0.05) -> Optional[List[Optional[Joint]]]:
        """Получение результата обработки"""
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def _read_results(self):
        """Поток чтения результатов из JSON файлов"""
        processed_files = set()
        
        while self.running:
            try:
                if os.path.exists(self.output_dir):
                    for root, dirs, files in os.walk(self.output_dir):
                        for f in files:
                            if f.endswith('.json') and f not in processed_files:
                                processed_files.add(f)
                                filepath = os.path.join(root, f)
                                try:
                                    with open(filepath, 'r') as json_file:
                                        data = json.load(json_file)
                                        joints = self._parse_json(data)
                                        if joints:
                                            self.result_queue.put(joints, block=False)
                                            print(f"Got result with {sum(1 for j in joints if j is not None)} joints")
                                except Exception as e:
                                    print(f"Error parsing JSON {f}: {e}")
            except Exception as e:
                print(f"Error reading results: {e}")
            
            time.sleep(0.05)
    
    def _parse_json(self, data: dict) -> List[Optional[Joint]]:
        """Парсинг JSON из OpenPose"""
        joints = [None] * 18  # 18 ключевых точек для COCO
        
        try:
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
                                name=self._get_joint_name(i)
                            )
        except Exception as e:
            print(f"Error parsing JSON data: {e}")
        
        return joints
    
    def _get_joint_name(self, idx: int) -> str:
        """Получение имени сустава по индексу (COCO формат)"""
        names = {
            0: "nose", 1: "neck", 2: "right_shoulder", 3: "right_elbow",
            4: "right_wrist", 5: "left_shoulder", 6: "left_elbow", 7: "left_wrist",
            8: "right_hip", 9: "right_knee", 10: "right_ankle", 11: "left_hip",
            12: "left_knee", 13: "left_ankle", 14: "right_eye", 15: "left_eye",
            16: "right_ear", 17: "left_ear"
        }
        return names.get(idx, f"joint_{idx}")
    
    def stop(self):
        """Остановка процессора"""
        print("Stopping OpenPose processor...")
        self.running = False
        
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        
        # Очищаем временные папки
        for dir_path in [self.input_dir, self.output_dir]:
            if dir_path and os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path, ignore_errors=True)
                except:
                    pass
        
        print("OpenPose processor stopped")