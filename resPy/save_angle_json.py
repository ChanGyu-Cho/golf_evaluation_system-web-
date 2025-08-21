import cv2
import mediapipe as mp
import csv

# 웹 호환 skeleton video 및 angle json 생성 함수 (analyze_golf_video.py에서 import용)
def process_with_skeleton(input_path, output_path, csv_path, json_path):
    # --- ffmpeg로 웹 호환 mp4로 재인코딩 (libx264/yuv420p/faststart) ---
    import shutil
    import subprocess
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path is not None:
        temp_out = str(output_path) + '.ffmpeg_tmp.mp4'
        cmd = [ffmpeg_path, '-y', '-i', str(output_path), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', temp_out]
        try:
            print(f"[ffmpeg] Re-encoding for web compatibility: {' '.join(cmd)}")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0 and os.path.exists(temp_out):
                os.replace(temp_out, output_path)
                print(f"[ffmpeg] Web-compatible mp4 saved: {output_path}")
            else:
                print(f"[ffmpeg] Re-encode failed: {result.stderr.decode(errors='ignore')}")
        except Exception as e:
            print(f"[ffmpeg] Exception during re-encode: {e}")
    else:
        print("[ffmpeg] ffmpeg not found in PATH. Skeleton video may not be web-compatible.")
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

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    if not out.isOpened():
        print('Error: VideoWriter failed to open with mp4v codec.')
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

            if results.pose_landmarks:
                landmark_coords = []
                for i, landmark in enumerate(results.pose_landmarks.landmark):
                    x = int(landmark.x * width)
                    y = int(landmark.y * height)
                    z = landmark.z
                    visibility = landmark.visibility
                    landmark_coords.extend([landmark.x, landmark.y, landmark.z, visibility])

                csv_writer.writerow([frame_count] + landmark_coords)

                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                          mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=1, circle_radius=1),
                                          mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=2))

                hip_shoulder_knee_ankle_indices = [11, 12, 23, 24, 25, 26, 27, 28]
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

    # CSV → JSON 변환 (각도 포함)
    save_angle_json(csv_path, json_path, fps)

    # JSON 파일이 실제로 생성됐는지 체크
    import os
    if not os.path.exists(json_path):
        print(f"[WARNING] JSON file not created: {json_path}. COM 정보 추가 및 후처리 생략.")
        return

    # JSON 파일에 COM 이동범위 및 안정성 정보 추가
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)

        data["com_movement"] = {
            "mean": {"x": com_mean[0], "y": com_mean[1], "z": com_mean[2]},
            "std": {"x": com_std[0], "y": com_std[1], "z": com_std[2]},
            "range": com_range,
            "stable": stable
        }

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
        data["com_stability_scores"] = com_stability_scores

        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[WARNING] Failed to update JSON with COM info: {e}")
        return

    print(f"Processed video saved to: {output_path}")
    print(f"CSV saved to: {csv_path}")
    print(f"JSON saved to: {json_path}")

    # --- ffmpeg로 웹 호환 mp4로 재인코딩 (libx264/yuv420p/faststart) ---
    import shutil
    import subprocess
    if not os.path.exists(output_path):
        print(f"[WARNING] Skeleton video not found for ffmpeg re-encode: {output_path}")
        return
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path is not None:
        temp_out = str(output_path) + '.ffmpeg_tmp.mp4'
        cmd = [ffmpeg_path, '-y', '-i', str(output_path), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', temp_out]
        try:
            print(f"[ffmpeg] Re-encoding for web compatibility: {' '.join(cmd)}")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0 and os.path.exists(temp_out):
                os.replace(temp_out, output_path)
                print(f"[ffmpeg] Web-compatible mp4 saved: {output_path}")
            else:
                print(f"[ffmpeg] Re-encode failed: {result.stderr.decode(errors='ignore')}")
        except Exception as e:
            print(f"[ffmpeg] Exception during re-encode: {e}")
    else:
        print("[ffmpeg] ffmpeg not found in PATH. Skeleton video may not be web-compatible.")
import sys
import os
import pandas as pd
import numpy as np
import math
import json

# COCO17 keypoint 이름 및 인덱스
COCO_KP = [
    "Nose", "LEye", "REye", "LEar", "REar", "LShoulder", "RShoulder", "LElbow", "RElbow",
    "LWrist", "RWrist", "LHip", "RHip", "LKnee", "RKnee", "LAnkle", "RAnkle"
]
COCO_IDX = {name: i for i, name in enumerate(COCO_KP)}

def calculate_angle_2d(joint_coords):
    AB = (joint_coords[0][0] - joint_coords[1][0], joint_coords[0][1] - joint_coords[1][1])
    BC = (joint_coords[2][0] - joint_coords[1][0], joint_coords[2][1] - joint_coords[1][1])
    dot_product = AB[0] * BC[0] + AB[1] * BC[1]
    magnitude_AB = math.sqrt(AB[0]**2 + AB[1]**2)
    magnitude_BC = math.sqrt(BC[0]**2 + BC[1]**2)
    if magnitude_AB * magnitude_BC == 0:
        return None
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
        return None
    cos_theta = dot_product / (magnitude_AB * magnitude_CB)
    angle_radians = math.acos(np.clip(cos_theta, -1.0, 1.0))
    return math.degrees(angle_radians)

def replace_nan_with_none(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    elif isinstance(obj, list):
        return [replace_nan_with_none(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: replace_nan_with_none(v) for k, v in obj.items()}
    else:
        return obj

def save_angle_json(csv_path, out_json_path, fps=30):
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[ERROR] Failed to read CSV {csv_path}: {e}")
        raise

    # coerce all columns to numeric where possible to avoid numpy ufunc type errors
    try:
        df = df.apply(lambda col: pd.to_numeric(col, errors='coerce'))
    except Exception as e:
        print(f"[WARN] Failed to coerce CSV columns to numeric: {e}")
    angle_data = []
    com_positions = []
    # Use the CSV 'frame' column when present so we preserve original video frame indices
    # detect CSV column format: OpenPose uses name_x/name_y/name_c, previous pipeline used x_0,y_0,z_0 style
    cols = set(df.columns)
    use_name_cols = any(f"{name}_x" in cols for name in COCO_KP)

    def safe_num(v):
        try:
            return float(v)
        except Exception:
            return np.nan

    for _, row in df.iterrows():
        # normalize frame value (may be string in some CSVs)
        frame_num = None
        if 'frame' in df.columns and not pd.isna(row.get('frame', None)):
            try:
                frame_num = int(safe_num(row.get('frame')))
            except Exception:
                frame_num = None
        frame_angles = {"frame": frame_num}
        if use_name_cols:
            def get2d(j):
                # coerce to numeric; return (x,y) floats or (np.nan,np.nan)
                x = safe_num(row.get(f"{j}_x", np.nan))
                y = safe_num(row.get(f"{j}_y", np.nan))
                return (x, y)
            def get3d(j):
                # OpenPose CSV typically has x,y,confidence but no z; return nan for z
                x = safe_num(row.get(f"{j}_x", np.nan))
                y = safe_num(row.get(f"{j}_y", np.nan))
                return [x, y, np.nan]
        else:
            def get2d(j):
                # fall back to index-based columns like x_0, y_0
                colx = f"x_{COCO_IDX[j]}"
                coly = f"y_{COCO_IDX[j]}"
                x = safe_num(row.get(colx, np.nan))
                y = safe_num(row.get(coly, np.nan))
                return (x, y)
            def get3d(j):
                colx = f"x_{COCO_IDX[j]}"
                coly = f"y_{COCO_IDX[j]}"
                colz = f"z_{COCO_IDX[j]}"
                x = safe_num(row.get(colx, np.nan))
                y = safe_num(row.get(coly, np.nan))
                z = safe_num(row.get(colz, np.nan))
                return [x, y, z]

        # 각도 계산 (COCO17 기준)
        frame_angles["left_elbow_flexion"] = calculate_angle_2d([
            get2d("LShoulder"), get2d("LElbow"), get2d("LWrist")
        ])
        frame_angles["right_elbow_flexion"] = calculate_angle_2d([
            get2d("RShoulder"), get2d("RElbow"), get2d("RWrist")
        ])
        frame_angles["left_knee_flexion"] = calculate_angle_2d([
            get2d("LHip"), get2d("LKnee"), get2d("LAnkle")
        ])
        frame_angles["right_knee_flexion"] = calculate_angle_2d([
            get2d("RHip"), get2d("RKnee"), get2d("RAnkle")
        ])
        frame_angles["left_hip_flexion"] = calculate_angle_3d([
            get3d("LShoulder"), get3d("LHip"), get3d("LKnee")
        ])
        frame_angles["right_hip_flexion"] = calculate_angle_3d([
            get3d("RShoulder"), get3d("RHip"), get3d("RKnee")
        ])
        frame_angles["left_shoulder_flexion"] = calculate_angle_2d([
            get2d("LHip"), get2d("LShoulder"), get2d("LElbow")
        ])
        frame_angles["right_shoulder_flexion"] = calculate_angle_2d([
            get2d("RHip"), get2d("RShoulder"), get2d("RElbow")
        ])

        # 골반 기울기 및 회전 (use get2d to support both CSV formats)
        rh_x, rh_y = get2d("RHip")
        lh_x, lh_y = get2d("LHip")
        try:
            p_list = safe_num(rh_y) - safe_num(lh_y)
        except Exception:
            p_list = np.nan
        try:
            p_rot = safe_num(rh_x) - safe_num(lh_x)
        except Exception:
            p_rot = np.nan
        frame_angles["pelvis_list"] = p_list
        frame_angles["pelvis_rotation"] = p_rot

        # COM (8개 점 평균)
        com_joints = ["LHip", "RHip", "LShoulder", "RShoulder", "LKnee", "RKnee", "LAnkle", "RAnkle"]
        com_coords = [get3d(j) for j in com_joints]
        com_array = np.array(com_coords)
        # nanmean will return nan if all values nan; handle later
        try:
            com_mean = np.nanmean(com_array, axis=0)
        except Exception:
            com_mean = np.array([np.nan, np.nan, np.nan])
        frame_angles["com"] = {"x": float(com_mean[0]) if not np.isnan(com_mean[0]) else None,
                               "y": float(com_mean[1]) if not np.isnan(com_mean[1]) else None,
                               "z": float(com_mean[2]) if not np.isnan(com_mean[2]) else None}
        com_positions.append(com_mean)
        angle_data.append(frame_angles)

    # NaN → None 변환 (initial)
    clean_data = replace_nan_with_none(angle_data)

    # --- Interpolate missing numeric values across frames ---
    # Build a frame-indexed map to allow filling gaps for frames without detections
    if not clean_data:
        clean_data = []
    else:
        frames = [int(x['frame']) for x in clean_data if x['frame'] is not None]
        # If the CSV did not include a 'frame' column, frames will be empty and
        # every angle entry keeps frame=None. Assign sequential frame indices
        # in that case so downstream code and the frontend have a usable frame key.
        if not frames and clean_data:
            for i, d in enumerate(clean_data):
                d['frame'] = i
            frames = list(range(len(clean_data)))
        if frames:
            min_f, max_f = min(frames), max(frames)
            full_frames = list(range(min_f, max_f + 1))

            # collect all numeric keys (excluding 'frame' and nested 'com')
            numeric_keys = set()
            for d in clean_data:
                for k, v in d.items():
                    if k == 'frame' or k == 'com':
                        continue
                    if isinstance(v, (int, float)) or v is None:
                        numeric_keys.add(k)

            # Flatten com into com_x/com_y/com_z for interpolation convenience
            for d in clean_data:
                com = d.get('com') or {}
                d['com_x'] = com.get('x') if com else None
                d['com_y'] = com.get('y') if com else None
                d['com_z'] = com.get('z') if com else None
                if 'com' in d:
                    del d['com']
            numeric_keys.update(['com_x', 'com_y', 'com_z'])

            # build dict: frame -> {key: value}
            by_frame = {int(d['frame']): d for d in clean_data if d['frame'] is not None}

            import math as _math
            def interp_series(keys, frames_list):
                # keys: name of key to interpolate
                xs = []
                ys = []
                for f in frames_list:
                    v = by_frame.get(f, {}).get(keys, None)
                    if v is None:
                        ys.append(np.nan)
                    else:
                        try:
                            ys.append(float(v))
                        except Exception:
                            ys.append(np.nan)
                    xs.append(f)
                ys = np.array(ys, dtype=float)
                # where valid
                valid = ~np.isnan(ys)
                if valid.sum() == 0:
                    return ys  # all nan, nothing to do
                if valid.sum() == 1:
                    # single value: fill with that value
                    ys[~valid] = ys[valid][0]
                    return ys
                # linear interpolation for interior points
                xp = np.array(xs)[valid]
                fp = ys[valid]
                yi = np.interp(xs, xp, fp)
                # preserve original NaN where both xp but np.interp fills edges; keep edges filled
                return yi

            filled_by_frame = {}
            for k in numeric_keys:
                vals = interp_series(k, full_frames)
                for idx, f in enumerate(full_frames):
                    filled_by_frame.setdefault(f, {})[k] = (float(vals[idx]) if not np.isnan(vals[idx]) else None)

            # reconstruct clean_data as full contiguous frames list using filled values
            new_clean = []
            for f in full_frames:
                entry = {'frame': f}
                for k in numeric_keys:
                    entry[k] = filled_by_frame.get(f, {}).get(k)
                # move back com_x/com_y/com_z into nested com for backward compatibility
                entry['com'] = {
                    'x': entry.pop('com_x', None),
                    'y': entry.pop('com_y', None),
                    'z': entry.pop('com_z', None)
                }
                # include other non-numeric keys from original if present (tags etc.)
                orig = by_frame.get(f, {})
                for ok, ov in orig.items():
                    if ok in ('frame', 'com'):
                        continue
                    if ok in numeric_keys:
                        continue
                    entry[ok] = ov
                new_clean.append(entry)
            clean_data = new_clean

    # After interpolation, recompute com_positions from the cleaned/interpolated data
    com_positions = []
    for d in clean_data:
        com = d.get('com') or {}
        com_positions.append([com.get('x', np.nan), com.get('y', np.nan), com.get('z', np.nan)])
    # COM 이동 범위, 안정성, 프레임별 score
    # Ensure we have a float ndarray: replace None with np.nan and coerce to float to avoid
    # numpy ufunc errors when the array dtype is object.
    com_positions_clean = []
    for row in com_positions:
        new_row = []
        for v in row:
            if v is None:
                new_row.append(np.nan)
            else:
                try:
                    new_row.append(float(v))
                except Exception:
                    new_row.append(np.nan)
        com_positions_clean.append(new_row)
    try:
        com_positions_np = np.array(com_positions_clean, dtype=float)
    except Exception:
        # Fallback: create an empty float array if conversion fails
        com_positions_np = np.array([], dtype=float).reshape((0, 3))
    if com_positions_np.size > 0 and not np.all(np.isnan(com_positions_np)):
        # mean/std ignoring NaNs
        com_mean = np.nanmean(com_positions_np, axis=0)
        com_std = np.nanstd(com_positions_np, axis=0)
        # ranges per-dim (None if entire dim is NaN)
        com_range = {
            'x_range': (float(np.nanmax(com_positions_np[:, 0]) - np.nanmin(com_positions_np[:, 0]))
                        if not np.all(np.isnan(com_positions_np[:, 0])) else None),
            'y_range': (float(np.nanmax(com_positions_np[:, 1]) - np.nanmin(com_positions_np[:, 1]))
                        if not np.all(np.isnan(com_positions_np[:, 1])) else None),
            'z_range': (float(np.nanmax(com_positions_np[:, 2]) - np.nanmin(com_positions_np[:, 2]))
                        if not np.all(np.isnan(com_positions_np[:, 2])) else None),
        }
        # Stability: prefer x/y when z missing. Require at least one dimension to evaluate.
        stability_threshold = 0.05
        dims_ok = []
        if com_range['x_range'] is not None:
            dims_ok.append(com_range['x_range'] < stability_threshold)
        if com_range['y_range'] is not None:
            dims_ok.append(com_range['y_range'] < stability_threshold)
        if com_range['z_range'] is not None:
            dims_ok.append(com_range['z_range'] < stability_threshold)
        stable = all(dims_ok) if dims_ok else False

        # Per-frame stability: compute Euclidean deviation using available dimensions per-frame
        com_stability_scores = []
        for i, row in enumerate(com_positions_np):
            # row is [x,y,z] possibly with NaNs; select dims that are valid in both row and mean
            valid_mask = ~np.isnan(row) & ~np.isnan(com_mean)
            if not valid_mask.any():
                deviation = None
            else:
                diffs = row[valid_mask] - com_mean[valid_mask]
                try:
                    deviation = float(np.linalg.norm(diffs))
                except Exception:
                    deviation = None
            com_stability_scores.append({"frame": i, "score": float(deviation) if deviation is not None else None})
    else:
        com_mean = [None, None, None]
        com_std = [None, None, None]
        com_range = {'x_range': None, 'y_range': None, 'z_range': None}
        stable = False
        com_stability_scores = []

    # compute a single COM stability metric (mean of per-frame deviations) and
    # remove per-frame 'com' entries from the angles output as requested
    # prepare per-frame COM frames list (use frame numbers from clean_data)
    com_frames = []
    for i, d in enumerate(clean_data):
        frm = d.get('frame', i)
        com = d.get('com') or {}
        com_frames.append({
            'frame': int(frm) if frm is not None else i,
            'x': (float(com.get('x')) if com.get('x') is not None else None),
            'y': (float(com.get('y')) if com.get('y') is not None else None),
            'z': (float(com.get('z')) if com.get('z') is not None else None)
        })

    scores_only = [s.get('score') for s in com_stability_scores if s.get('score') is not None]
    if scores_only:
        try:
            com_stability_mean = float(np.nanmean(np.array(scores_only, dtype=float)))
        except Exception:
            com_stability_mean = None
    else:
        com_stability_mean = None

    # remove per-frame 'com' from cleaned angle entries (user requested dropping per-frame COM x/y/z)
    for entry in clean_data:
        if isinstance(entry, dict) and 'com' in entry:
            entry.pop('com', None)

    output = {
        "fps": fps,
        "angles": clean_data,
        "com_movement": {
            "mean": {"x": (float(com_mean[0]) if com_mean[0] is not None and not np.isnan(com_mean[0]) else None),
                      "y": (float(com_mean[1]) if com_mean[1] is not None and not np.isnan(com_mean[1]) else None),
                      "z": (float(com_mean[2]) if com_mean[2] is not None and not np.isnan(com_mean[2]) else None)},
            "std": {"x": (float(com_std[0]) if com_std[0] is not None and not np.isnan(com_std[0]) else None),
                    "y": (float(com_std[1]) if com_std[1] is not None and not np.isnan(com_std[1]) else None),
                    "z": (float(com_std[2]) if com_std[2] is not None and not np.isnan(com_std[2]) else None)},
            "range": com_range,
            "stable": stable
        },
        # single metric summarizing COM stability (mean deviation). Lower is more stable.
        "com_stability": com_stability_mean
    }

    # attach per-frame COM coordinates and per-frame stability scores so frontend can plot them
    output["com_frames"] = com_frames
    output["com_stability_scores"] = com_stability_scores

    # Write output JSON
    try:
        with open(out_json_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Saved angle json: {out_json_path}")
    except Exception as e:
        print(f"[ERROR] Failed to write angle json {out_json_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python save_angle_json.py <input_csv> <output_json> [fps]")
        sys.exit(1)
    csv_path = sys.argv[1]
    out_json_path = sys.argv[2]
    fps = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    save_angle_json(csv_path, out_json_path, fps)
