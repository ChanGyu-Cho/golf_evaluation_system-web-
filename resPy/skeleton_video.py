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

    for _, row in df.iterrows():
        frame_angles = {"frame": int(row["frame"])}

        def get_coords(joint_name):
            idx = mp_joints[joint_name]
            return [row[f'x_{idx}'], row[f'y_{idx}'], row[f'z_{idx}']]

        # 3D 각도 계산
        frame_angles["left_elbow_flexion"] = calculate_angle_3d([
            get_coords("L_SHOULDER"),
            get_coords("L_ELBOW"),
            get_coords("L_WRIST"),
        ])
        frame_angles["right_elbow_flexion"] = calculate_angle_3d([
            get_coords("R_SHOULDER"),
            get_coords("R_ELBOW"),
            get_coords("R_WRIST"),
        ])
        frame_angles["left_knee_flexion"] = calculate_angle_3d([
            get_coords("L_HIP"),
            get_coords("L_KNEE"),
            get_coords("L_ANKLE"),
        ])
        frame_angles["right_knee_flexion"] = calculate_angle_3d([
            get_coords("R_HIP"),
            get_coords("R_KNEE"),
            get_coords("R_ANKLE"),
        ])
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

        # 2D 각도 예시 (Y-Z 평면)
        frame_angles["left_shoulder_flexion"] = calculate_angle_2d([
            [row[f'y_{mp_joints["L_HIP"]}'], row[f'z_{mp_joints["L_HIP"]}']],
            [row[f'y_{mp_joints["L_SHOULDER"]}'], row[f'z_{mp_joints["L_SHOULDER"]}']],
            [row[f'y_{mp_joints["L_ELBOW"]}'], row[f'z_{mp_joints["L_ELBOW"]}']],
        ])
        frame_angles["right_shoulder_flexion"] = calculate_angle_2d([
            [row[f'y_{mp_joints["R_HIP"]}'], row[f'z_{mp_joints["R_HIP"]}']],
            [row[f'y_{mp_joints["R_SHOULDER"]}'], row[f'z_{mp_joints["R_SHOULDER"]}']],
            [row[f'y_{mp_joints["R_ELBOW"]}'], row[f'z_{mp_joints["R_ELBOW"]}']],
        ])

        frame_angles["pelvis_list"] = row[f'y_{mp_joints["R_HIP"]}'] - row[f'y_{mp_joints["L_HIP"]}']
        frame_angles["pelvis_rotation"] = row[f'x_{mp_joints["R_HIP"]}'] - row[f'x_{mp_joints["L_HIP"]}']

        angle_data.append(frame_angles)

    return angle_data

def csv_to_precomputed_landmark_json(csv_path, json_path):
    df = pd.read_csv(csv_path)
    angle_data = add_joint_angles_from_csv(df)
    with open(json_path, 'w') as f:
        json.dump(angle_data, f, indent=2)
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
        header += [f'x_{i}', f'y_{i}', f'z_{i}', f'visibility_{i}']
    csv_writer.writerow(header)

    landmark_drawing_spec = mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=5, circle_radius=6)
    connection_drawing_spec = mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=3, circle_radius=2)

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    image,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=landmark_drawing_spec,
                    connection_drawing_spec=connection_drawing_spec,
                )

                row = [frame_idx]
                for lm in results.pose_landmarks.landmark:
                    row.extend([lm.x, lm.y, lm.z, lm.visibility])
                csv_writer.writerow(row)
            else:
                nan = float('nan')
                row = [frame_idx] + [nan] * 33 * 4
                csv_writer.writerow(row)

            if (orig_width, orig_height) != (width, height):
                image = cv2.resize(image, (width, height))

            out.write(image)
            frame_idx += 1

    csv_file.close()
    cap.release()
    out.release()

    # CSV 완료 후 JSON 생성
    csv_to_precomputed_landmark_json(csv_path, json_path)


if __name__ == "__main__":
    input_video = sys.argv[1]
    output_video = sys.argv[2]
    output_csv = sys.argv[3]
    output_json = sys.argv[4]  # 새로 추가된 인자

    process_with_skeleton(input_video, output_video, output_csv, output_json)
