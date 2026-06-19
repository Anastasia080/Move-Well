"""
Модуль для анализа позы через OpenPose (OpenCV DNN backend).
Использует оригинальные веса OpenPose BODY_25 через cv2.dnn.
"""

import cv2
import numpy as np
import os
from typing import List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Joint:
    x: float
    y: float
    confidence: float
    name: str


class PoseAnalyzer:
    """Анализатор позы: OpenPose BODY_25 через OpenCV DNN."""

    # COCO: 18 точек тела
    JOINT_NAMES = {
        0: "nose", 1: "neck",
        2: "right_shoulder", 3: "right_elbow", 4: "right_wrist",
        5: "left_shoulder",  6: "left_elbow",  7: "left_wrist",
        8: "right_hip",  9: "right_knee",  10: "right_ankle",
        11: "left_hip",  12: "left_knee",  13: "left_ankle",
        14: "right_eye", 15: "left_eye",
        16: "right_ear", 17: "left_ear",
    }

    SKELETON_CONNECTIONS = [
        (1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7),         # руки
        (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13),    # ноги
        (1, 0), (0, 14), (14, 16), (0, 15), (15, 17),            # голова
    ]

    NUM_KEYPOINTS = 18
    # COCO: каналы 0-17 — хитмапы для 18 точек; канал 18 — фон.
    _HEATMAP_OFFSET = 0

    # Размер входа сети (должен делиться на 8)
    _NET_INPUT_SIZE = (368, 368)

    def __init__(self, openpose_path: str = None, confidence_threshold: float = 0.3):
        model_dir = (
            Path(openpose_path) / "models" / "pose" / "body_25"
            if openpose_path
            else Path(__file__).parent.parent.parent / "openpose" / "models" / "pose" / "body_25"
        )

        prototxt = str(model_dir / "pose_deploy_linevec.prototxt")
        caffemodel = str(model_dir / "pose_iter_440000.caffemodel")

        if not os.path.exists(caffemodel):
            raise FileNotFoundError(f"OpenPose caffemodel not found: {caffemodel}")
        if not os.path.exists(prototxt):
            raise FileNotFoundError(f"OpenPose prototxt not found: {prototxt}")

        self.net = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)
        self.confidence_threshold = confidence_threshold
        print(f"PoseAnalyzer ready (OpenCV DNN + OpenPose COCO 18)")

    def analyze_image(self, image: np.ndarray) -> Tuple[List[Optional[Joint]], np.ndarray]:
        h, w = image.shape[:2]
        net_w, net_h = self._NET_INPUT_SIZE

        blob = cv2.dnn.blobFromImage(
            image, 1.0 / 255.0, (net_w, net_h), (0, 0, 0), swapRB=False, crop=False
        )
        self.net.setInput(blob)
        output = self.net.forward()  # (1, 78, out_h, out_w)

        out_h = output.shape[2]
        out_w = output.shape[3]

        joints: List[Optional[Joint]] = []
        for i in range(self.NUM_KEYPOINTS):
            heatmap = output[0, self._HEATMAP_OFFSET + i, :, :]
            _, confidence, _, point = cv2.minMaxLoc(heatmap)

            if confidence > self.confidence_threshold:
                x = int(point[0] * w / out_w)
                y = int(point[1] * h / out_h)
                joints.append(Joint(
                    x=x, y=y,
                    confidence=float(confidence),
                    name=self.JOINT_NAMES.get(i, f"joint_{i}"),
                ))
            else:
                joints.append(None)

        visible = sum(1 for j in joints if j is not None)
        print(f"Visible joints: {visible}/{self.NUM_KEYPOINTS}")

        return joints, self.draw_skeleton(image, joints)

    def analyze_video_frame(self, frame: np.ndarray) -> List[Optional[Joint]]:
        return self.analyze_image(frame)[0]

    def draw_skeleton(self, image: np.ndarray, joints: List[Optional[Joint]]) -> np.ndarray:
        img = image.copy()
        h, w = img.shape[:2]

        for i, joint in enumerate(joints):
            if joint is not None:
                x, y = int(joint.x), int(joint.y)
                if 0 <= x < w and 0 <= y < h:
                    color = (0, int(255 * min(joint.confidence, 1.0)), 0)
                    cv2.circle(img, (x, y), 5, color, -1)
                    cv2.putText(img, str(i), (x + 5, y - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        for start, end in self.SKELETON_CONNECTIONS:
            if start < len(joints) and end < len(joints):
                j1, j2 = joints[start], joints[end]
                if j1 and j2:
                    x1, y1 = int(j1.x), int(j1.y)
                    x2, y2 = int(j2.x), int(j2.y)
                    if 0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h:
                        cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

        return img

    def calculate_angle(self, joint_a: Joint, joint_b: Joint, joint_c: Joint) -> float:
        a = np.array([joint_a.x, joint_a.y])
        b = np.array([joint_b.x, joint_b.y])
        c = np.array([joint_c.x, joint_c.y])

        ba = a - b
        bc = c - b
        cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
        return float(np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0))))
