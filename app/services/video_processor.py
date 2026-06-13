"""
Видео процессор для OpenPose
"""

import subprocess
import os
import tempfile
import shutil
from typing import Optional
import uuid

class VideoProcessor:
    """Обработка видео через OpenPose"""
    
    def __init__(self, openpose_path: str = r"D:\openpose\openpose"):
        self.openpose_path = openpose_path
        self.openpose_exe = os.path.join(openpose_path, "bin", "OpenPoseDemo.exe")
        
        if not os.path.exists(self.openpose_exe):
            raise FileNotFoundError(f"OpenPose not found: {self.openpose_exe}")
        
        # Создаём папку для результатов
        self.output_dir = "processed_videos"
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"✅ VideoProcessor initialized")
    
    def process_video(self, input_video_path: str) -> Optional[str]:
        """
        Обработка видео через OpenPose
        
        Args:
            input_video_path: путь к исходному видео
            
        Returns:
            путь к обработанному видео (со скелетом)
        """
        # Генерируем уникальное имя для выходного видео
        video_id = str(uuid.uuid4())[:8]
        output_video_path = os.path.join(self.output_dir, f"processed_{video_id}.avi")
        
        # Команда для OpenPose
        cmd = [
            self.openpose_exe,
            "--video", input_video_path,
            "--write_video", output_video_path,
            "--display", "0",
            "--model_pose", "COCO",
            "--num_gpu", "0",
            "--render_pose", "1"
        ]
        
        print(f"🚀 Processing video: {input_video_path}")
        print(f"📤 Output: {output_video_path}")
        
        try:
            # Запускаем OpenPose
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 минут на обработку
            )
            
            if result.returncode == 0 and os.path.exists(output_video_path):
                print(f"✅ Video processed successfully")
                return output_video_path
            else:
                print(f"❌ OpenPose error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ Video processing timeout")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def cleanup(self, video_path: str):
        """Удаление временного видео"""
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                print(f"🗑️ Deleted: {video_path}")
        except Exception as e:
            print(f"Error deleting: {e}")