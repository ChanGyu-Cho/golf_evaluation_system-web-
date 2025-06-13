import cv2
import mediapipe as mp
import sys
import csv
import math
import pandas as pd
import numpy as np
import json


def calculate_angle_2d(joint_coords, num=3):
    if num == 3:
        AB = (joint_coords[0][0] - joint_coords[1][0], joint_coords[0][1] - joint_coords[1][1])
        BC = (joint_coords[2][0] - joint_coords[1][0], joint_coords[2][1] - joint_coords[1][1])
    else:
        AB = (joint_coords[0][0] - joint_coords[1][0], joint_coords[0][1] - joint_coords[1][1])
        BC = (joint_coords[2][0] - joint_coords[3][0], joint_coords[2][1] - joint_coords[3][1])

    dot_product = AB[0] * BC[0] + AB[1] * BC[1]
    magnitude_AB = math.sqrt(AB[0]**2 + AB[1]**2)
    magnitude_BC = math.sqrt(BC[0]**2 + BC[1]**2)

    if magnitude_AB * magnitude_BC == 0:
        return float('nan')

    cos_theta = dot_product / (magnitude_AB * magnitude_BC)
    angle_radians = math.acos(np.clip(cos_theta, -1.0, 1.0))
    return math.degrees(angle_radians)


def calculate_angle_3d(joint_coords):
    A = np.array(joint_coords[0])
    B = np.array(joint_coords[1])
    C = np.array(joint_coords[2])

    AB = A - B
    CB = C - B

    dot_product = np.dot(AB, CB)
    magnitude_AB = np.linalg.norm(AB)
    magnitude_CB = np.linalg.norm(CB)

    if magnitude_AB * magnitude_CB == 0:
        return float('nan')

    cos_theta = dot_product / (magnitude_AB * magnitude_CB)
    angle_radians = math.acos(np.clip(cos_theta, -1.0, 1.0))
    return math.degrees(angle_radians)


mp_joints = {
    "L_SHOULDER": 11,
    "R_SHOULDER": 12,
    "L_ELBOW": 13,
    "R_ELBOW": 14,
    "L_WRIST": 15,
    "R_WRIST": 16,
    "L_HIP": 23,
    "R_HIP": 24,
    "L_KNEE": 25,
    "R_KNEE": 26,
    "L_ANKLE": 27,
    "R_ANKLE": 28,
}


def add_joint_angles_from_csv(df):
    angle_data = []

    com_joints = [
        "L_HIP", "R_HIP", "L_SHOULDER", "R_SHOULDER",
        "L_KNEE", "R_KNEE", "L_ANKLE", "R_ANKLE"
    ]

    for _, row in df.iterrows():
        frame_angles = {"frame": int(row["frame"])}

        def get_coords(joint_name):
            idx = mp_joints[joint_name]
            return [row[f'x_{idx}'], row[f'y_{idx}'], row[f'z_{idx}']]

        def get_coords_2d(joint_name, axes=('y', 'z')):
            idx = mp_joints[joint_name]
            return [row[f'{axes[0]}_{idx}'], row[f'{axes[1]}_{idx}']]

        # 2D 각도
        frame_angles["left_elbow_flexion"] = calculate_angle_2d([
            get_coords_2d("L_SHOULDER"),
            get_coords_2d("L_ELBOW"),
            get_coords_2d("L_WRIST"),
        ])
        frame_angles["right_elbow_flexion"] = calculate_angle_2d([
            get_coords_2d("R_SHOULDER"),
            get_coords_2d("R_ELBOW"),
            get_coords_2d("R_WRIST"),
        ])
        frame_angles["left_knee_flexion"] = calculate_angle_2d([
            get_coords_2d("L_HIP"),
            get_coords_2d("L_KNEE"),
            get_coords_2d("L_ANKLE"),
        ])
        frame_angles["right_knee_flexion"] = calculate_angle_2d([
            get_coords_2d("R_HIP"),
            get_coords_2d("R_KNEE"),
            get_coords_2d("R_ANKLE"),
        ])
        # 3D 엉덩이
        frame_angles["left_hip_flexion"] = calculate_angle_3d([
            get_coords("L_SHOULDER"),
            get_coords("L_HIP"),
            get_coords("L_KNEE"),
        ])
        frame_angles["right_hip_flexion"] = calculate_angle_3d([
            get_coords("R_SHOULDER"),
            get_coords("R_HIP"),
            get_coords("R_KNEE"),
        ])
        # 어깨
        frame_angles["left_shoulder_flexion"] = calculate_angle_2d([
            get_coords_2d("L_HIP"),
            get_coords_2d("L_SHOULDER"),
            get_coords_2d("L_ELBOW"),
        ])
        frame_angles["right_shoulder_flexion"] = calculate_angle_2d([
            get_coords_2d("R_HIP"),
            get_coords_2d("R_SHOULDER"),
            get_coords_2d("R_ELBOW"),
        ])
        # 골반 기울기
        frame_angles["pelvis_list"] = row[f'y_{mp_joints["R_HIP"]}'] - row[f'y_{mp_joints["L_HIP"]}']
        frame_angles["pelvis_rotation"] = row[f'x_{mp_joints["R_HIP"]}'] - row[f'x_{mp_joints["L_HIP"]}']

        # COM
        com_coords = [get_coords(j) for j in com_joints]
        com_array = np.array(com_coords)
        com_mean = np.nanmean(com_array, axis=0)

        frame_angles["com"] = {
            "x": com_mean[0],
            "y": com_mean[1],
            "z": com_mean[2]
        }

        angle_data.append(frame_angles)

    return angle_data

# NaN → None
def replace_nan_with_none(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    elif isinstance(obj, list):
        return [replace_nan_with_none(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: replace_nan_with_none(v) for k, v in obj.items()}
    else:
        return obj

def csv_to_precomputed_landmark_json(csv_path, json_path, fps):
    df = pd.read_csv(csv_path)
    angle_data = add_joint_angles_from_csv(df)

    # com 제거
    for frame in angle_data:
        if 'com' in frame:
            del frame['com']

    clean_data = replace_nan_with_none(angle_data)

    output = {
        "fps": fps,
        "angles": clean_data
    }

    with open(json_path, 'w') as f:
        json.dump(output, f, indent=2, allow_nan=False)

    print(f"Saved JSON: {json_path}")

def process_with_skeleton(input_path, output_path, csv_path, json_path):
    mp_drawing = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose

    cap = cv2.VideoCapture(input_path)
    orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    max_width, max_height = 1920, 1080
    if orig_width > max_width or orig_height > max_height:
        width_ratio = max_width / orig_width
        height_ratio = max_height / orig_height
        scale = min(width_ratio, height_ratio)
        width = int(orig_width * scale)
        height = int(orig_height * scale)
    else:
        width, height = orig_width, orig_height

    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    if not out.isOpened():
        print("VideoWriter failed to open with H.264 codec. Fallback to mp4v")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        if not out.isOpened():
            print("Error: VideoWriter failed to open even with mp4v codec.")
            cap.release()
            return

    csv_file = open(csv_path, mode='w', newline='')
    csv_writer = csv.writer(csv_file)

    header = ['frame']
    for i in range(33):
        header.extend([f'x_{i}', f'y_{i}', f'z_{i}', f'visibility_{i}'])
    csv_writer.writerow(header)

    com_positions = []

    with mp_pose.Pose(static_image_mode=False,
                      model_complexity=2,
                      enable_segmentation=False,
                      min_detection_confidence=0.7,
                      min_tracking_confidence=0.7) as pose:

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if width != orig_width or height != orig_height:
                frame = cv2.resize(frame, (width, height))

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            landmark_coords = []

            if results.pose_landmarks:
                for i, landmark in enumerate(results.pose_landmarks.landmark):
                    landmark_coords.extend([landmark.x, landmark.y, landmark.z, landmark.visibility])

                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                          mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=1, circle_radius=1),
                                          mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=2))

                # COM 계산
                hip_shoulder_knee_ankle_indices = [mp_joints[j] for j in [
                    "L_HIP", "R_HIP", "L_SHOULDER", "R_SHOULDER",
                    "L_KNEE", "R_KNEE", "L_ANKLE", "R_ANKLE"
                ]]
                xs = [results.pose_landmarks.landmark[i].x for i in hip_shoulder_knee_ankle_indices]
                ys = [results.pose_landmarks.landmark[i].y for i in hip_shoulder_knee_ankle_indices]
                zs = [results.pose_landmarks.landmark[i].z for i in hip_shoulder_knee_ankle_indices]

                com_x = np.mean(xs)
                com_y = np.mean(ys)
                com_z = np.mean(zs)
                com_positions.append((com_x, com_y, com_z))

                com_px = int(com_x * width)
                com_py = int(com_y * height)
                cv2.circle(image, (com_px, com_py), 8, (0, 255, 0), -1)
            else:
                # 관절 없는 경우 → NaN 기록 (중요!)
                for i in range(33):
                    landmark_coords.extend([float('nan'), float('nan'), float('nan'), float('nan')])

            csv_writer.writerow([frame_count] + landmark_coords)
            out.write(image)
            frame_count += 1

    cap.release()
    out.release()
    csv_file.close()

    com_positions_np = np.array(com_positions)
    if len(com_positions_np) > 0:
        com_mean = np.mean(com_positions_np, axis=0)
        com_std = np.std(com_positions_np, axis=0)
        com_range = {
            'x_range': float(np.ptp(com_positions_np[:, 0])),
            'y_range': float(np.ptp(com_positions_np[:, 1])),
            'z_range': float(np.ptp(com_positions_np[:, 2])),
        }
        stability_threshold = 0.05
        stable = (com_range['x_range'] < stability_threshold and
                  com_range['y_range'] < stability_threshold and
                  com_range['z_range'] < stability_threshold)
    else:
        com_mean = [None, None, None]
        com_std = [None, None, None]
        com_range = {'x_range': None, 'y_range': None, 'z_range': None}
        stable = False

    csv_to_precomputed_landmark_json(csv_path, json_path, fps)

    with open(json_path, 'r') as f:
        data = json.load(f)

    com_stability_scores = []
    if len(com_positions_np) > 0:
        for i, (x, y, z) in enumerate(com_positions_np):
            deviation = math.sqrt(
                (x - com_mean[0]) ** 2 +
                (y - com_mean[1]) ** 2 +
                (z - com_mean[2]) ** 2
            )
            com_stability_scores.append({
                "frame": i,
                "score": deviation
            })

    data["com_movement"] = {
        "mean": {"x": com_mean[0], "y": com_mean[1], "z": com_mean[2]},
        "std": {"x": com_std[0], "y": com_std[1], "z": com_std[2]},
        "range": com_range,
        "stable": stable
    }
    data["com_stability_scores"] = com_stability_scores

    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Processed video saved to: {output_path}")
    print(f"CSV saved to: {csv_path}")
    print(f"JSON saved to: {json_path}")

if __name__ == "__main__":
    input_video_path = sys.argv[1]
    output_video_path = sys.argv[2]
    output_csv_path = sys.argv[3]
    output_json_path = sys.argv[4]

    process_with_skeleton(input_video_path, output_video_path, output_csv_path, output_json_path)