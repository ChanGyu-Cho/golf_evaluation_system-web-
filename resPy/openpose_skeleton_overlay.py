import cv2
import numpy as np
import pandas as pd
import argparse
import json

def draw_openpose_skeleton(frame, keypoints, connections=None, names=None, color=(0,255,0), thickness=2, draw_lines=True):
    """
    Draw skeleton on frame.
    - keypoints: (N,2) ndarray
    - connections: list of (i,j) pairs (optional)
    - names: optional list of strings for labeling each keypoint
    - draw_lines: if False, only draw points and labels
    """
    # draw connections first (if enabled)
    if draw_lines and connections is not None:
        for i, j in connections:
            if i < 0 or j < 0 or i >= len(keypoints) or j >= len(keypoints):
                continue
            if np.all(keypoints[i] >= 0) and np.all(keypoints[j] >= 0):
                pt1 = tuple(int(x) for x in keypoints[i])
                pt2 = tuple(int(x) for x in keypoints[j])
                cv2.line(frame, pt1, pt2, color, thickness)

    # draw keypoints and optional labels
    for idx, pt in enumerate(keypoints):
        if not np.all(pt >= 0):
            continue
        p = tuple(int(x) for x in pt)
        # draw only a red filled circle (no text labels)
        cv2.circle(frame, p, 4, (0,0,255), -1)
    return frame

# Canonical COCO17 keypoint connections (0-indexed)
# Reference mapping: 0:Nose,1:LEye,2:REye,3:LEar,4:REar,5:LShoulder,6:RShoulder,7:LElbow,8:RElbow,
# 9:LWrist,10:RWrist,11:LHip,12:RHip,13:LKnee,14:RKnee,15:LAnkle,16:RAnkle
COCO_CONNECTIONS = [
    (0,1),(0,2),(1,3),(2,4),
    (5,6),(5,7),(7,9),(6,8),(8,10),
    (5,11),(6,12),(11,12),
    (11,13),(13,15),(12,14),(14,16)
]

def openpose_skeleton_overlay(
    input_video_path, csv_path, output_video_path, fourcc_code='avc1', points_only=False):
    cap = cv2.VideoCapture(input_video_path)
    df = pd.read_csv(csv_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    if not out.isOpened():
        print(f'Warning: VideoWriter failed with {fourcc_code}, fallback to mp4v')
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        if not out.isOpened():
            print('Error: VideoWriter failed to open. Abort.')
            cap.release()
            return
    frame_idx = 0
    # 오직 openpose COCO17 포맷(x_0~x_16, y_0~y_16, score_0~16)만 지원
    V = 17
    COCO_NAMES = [
        "Nose", "LEye", "REye", "LEar", "REar", "LShoulder", "RShoulder", "LElbow", "RElbow",
        "LWrist", "RWrist", "LHip", "RHip", "LKnee", "RKnee", "LAnkle", "RAnkle"
    ]
    # 우선 x_0~x_16, ... 포맷 시도
    x_cols = [f"x_{i}" for i in range(V)]
    y_cols = [f"y_{i}" for i in range(V)]
    score_cols = [f"score_{i}" for i in range(V)]
    # Determine whether CSV stores normalized coords (0..1) or absolute pixels (>1)
    def _is_normalized(columns_x):
        # safe check: if max value across the column set <= 1.0 -> normalized
        try:
            vals = df[columns_x].replace([float('inf'), -float('inf')], pd.NA).dropna(how='all')
            if vals.size == 0:
                return False
            mx = vals.to_numpy(dtype=float).max()
            return mx <= 1.0
        except Exception:
            return False

    if all(col in df.columns for col in x_cols) and all(col in df.columns for col in y_cols) and all(col in df.columns for col in score_cols):
        normalized = _is_normalized(x_cols)
        def get_keypoints(idx):
            pts = []
            for i in range(V):
                xv = df.at[idx, f'x_{i}']
                yv = df.at[idx, f'y_{i}']
                sc = df.at[idx, f'score_{i}'] if f'score_{i}' in df.columns else None
                # treat NaN, 0, or low-confidence as missing
                if pd.isna(xv) or pd.isna(yv) or (not pd.isna(sc) and float(sc) <= 0.01) or (xv == 0 and yv == 0):
                    pts.append([-1, -1])
                    continue
                try:
                    xv = float(xv)
                    yv = float(yv)
                except Exception:
                    pts.append([-1, -1]); continue
                if normalized:
                    pts.append([xv * width, yv * height])
                else:
                    pts.append([xv, yv])
            return np.array(pts)
    # COCO 관절명 기반 포맷 지원 (Nose_x, ...)
    elif all(f"{name}_x" in df.columns for name in COCO_NAMES) and all(f"{name}_y" in df.columns for name in COCO_NAMES) and all(f"{name}_c" in df.columns for name in COCO_NAMES):
        name_x_cols = [f"{name}_x" for name in COCO_NAMES]
        normalized = _is_normalized(name_x_cols)
        def get_keypoints(idx):
            pts = []
            for name in COCO_NAMES:
                xv = df.at[idx, f'{name}_x']
                yv = df.at[idx, f'{name}_y']
                sc = df.at[idx, f'{name}_c'] if f'{name}_c' in df.columns else None
                if pd.isna(xv) or pd.isna(yv) or (not pd.isna(sc) and float(sc) <= 0.01) or (xv == 0 and yv == 0):
                    pts.append([-1, -1])
                    continue
                try:
                    xv = float(xv)
                    yv = float(yv)
                except Exception:
                    pts.append([-1, -1]); continue
                if normalized:
                    pts.append([xv * width, yv * height])
                else:
                    pts.append([xv, yv])
            return np.array(pts)
    else:
        raise KeyError('CSV는 반드시 openpose COCO17 포맷(x_0~x_16, y_0~x_16, score_0~16) 또는 (Nose_x, ..., RAnkle_c) 포맷이어야 합니다.')

    while True:
        ret, frame = cap.read()
        if not ret or frame_idx >= len(df):
            break
        keypoints = get_keypoints(frame_idx)
        # If user mapping is provided, draw in user-index space
        if hasattr(openpose_skeleton_overlay, '_user_connections') and openpose_skeleton_overlay._user_connections is not None:
            # build user_kp array from coco-ordered keypoints
            coco_to_user = openpose_skeleton_overlay._coco_to_user
            max_user = openpose_skeleton_overlay._max_user_index
            user_kp = [[-1, -1] for _ in range(max_user+1)]
            for coco_idx in range(len(keypoints)):
                if coco_idx in coco_to_user:
                    uidx = coco_to_user[coco_idx]
                    user_kp[uidx] = [float(keypoints[coco_idx][0]), float(keypoints[coco_idx][1])]
            # prepare user names (mapped COCO names where available)
            user_names = [str(i) for i in range(max_user+1)]
            if hasattr(openpose_skeleton_overlay, '_user_name_map') and openpose_skeleton_overlay._user_name_map is not None:
                for uidx, name in openpose_skeleton_overlay._user_name_map.items():
                    if uidx >= 0 and uidx < len(user_names):
                        user_names[uidx] = name
            frame = draw_openpose_skeleton(frame, np.array(user_kp), openpose_skeleton_overlay._user_connections, names=user_names, draw_lines=(not points_only))
        else:
            frame = draw_openpose_skeleton(frame, keypoints, COCO_CONNECTIONS, names=COCO_NAMES, draw_lines=(not points_only))
        out.write(frame)
        frame_idx += 1
    cap.release()
    out.release()
    print(f'OpenPose skeleton overlay video saved: {output_video_path}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_video', help='input video path')
    parser.add_argument('csv', help='csv keypoints path')
    parser.add_argument('output_video', help='output overlay video path')
    parser.add_argument('--map', dest='map_json', help='optional JSON file mapping user_index->coco_index', default=None)
    parser.add_argument('--impute', dest='impute', action='store_true', help='enable temporal imputation for missing keypoints')
    parser.add_argument('--points-only', dest='points_only', action='store_true', help='draw only points and labels; do not draw connecting lines')
    args = parser.parse_args()

    # if imputation requested, perform simple temporal interpolation for x/y columns
    if args.impute:
        try:
            # find x/y columns
            V = 17
            x_cols = [f"x_{i}" for i in range(V)]
            y_cols = [f"y_{i}" for i in range(V)]
            # if CSV uses name_x format, detect and use those
            sample_df = pd.read_csv(args.csv, nrows=1)
            if not all(col in sample_df.columns for col in x_cols):
                # try COCO_NAMES style
                COCO_NAMES = [
                    "Nose", "LEye", "REye", "LEar", "REar", "LShoulder", "RShoulder",
                    "LElbow", "RElbow", "LWrist", "RWrist", "LHip", "RHip", "LKnee",
                    "RKnee", "LAnkle", "RAnkle"
                ]
                x_cols = [f"{n}_x" for n in COCO_NAMES]
                y_cols = [f"{n}_y" for n in COCO_NAMES]
            df_all = pd.read_csv(args.csv)
            # treat (0,0) as missing
            for xc,yc in zip(x_cols, y_cols):
                df_all.loc[(df_all[xc]==0)&(df_all[yc]==0), xc] = np.nan
                df_all.loc[(df_all[xc]==0)&(df_all[yc]==0), yc] = np.nan
            # interpolate per column
            df_all[x_cols] = df_all[x_cols].astype(float).interpolate(method='linear', limit_direction='both')
            df_all[y_cols] = df_all[y_cols].astype(float).interpolate(method='linear', limit_direction='both')
            # fill remaining NaN with nearest valid (ffill/bfill)
            df_all[x_cols] = df_all[x_cols].fillna(method='ffill').fillna(method='bfill')
            df_all[y_cols] = df_all[y_cols].fillna(method='ffill').fillna(method='bfill')
            # write back temp csv to use for processing
            tmp_csv = args.csv + '.imputed.tmp'
            df_all.to_csv(tmp_csv, index=False)
            csv_to_use = tmp_csv
        except Exception as e:
            print('Imputation failed:', e)
            csv_to_use = args.csv
    else:
        csv_to_use = args.csv

    # load optional mapping
    user_map = None
    if args.map_json:
        try:
            with open(args.map_json, 'r', encoding='utf-8') as mf:
                user_map = json.load(mf)
            # convert keys/values to ints
            user_map = {int(k): int(v) for k,v in user_map.items()}
        except Exception as e:
            print('Failed to load mapping JSON:', e)
            user_map = None

    # if mapping provided, prepare helper attributes for overlay function
    if user_map:
        # build coco_to_user mapping
        coco_to_user = {}
        for user_idx, coco_idx in user_map.items():
            coco_to_user[coco_idx] = user_idx
        # build user connections from COCO_CONNECTIONS using coco_to_user
        user_connections = []
        for a,b in COCO_CONNECTIONS:
            if a in coco_to_user and b in coco_to_user:
                user_connections.append((coco_to_user[a], coco_to_user[b]))
        openpose_skeleton_overlay._user_connections = user_connections
        openpose_skeleton_overlay._coco_to_user = coco_to_user
        openpose_skeleton_overlay._max_user_index = max(user_map.keys())
        # prepare optional user name map for labels
        user_name_map = {}
        for user_idx, coco_idx in user_map.items():
            if 0 <= coco_idx < len(COCO_NAMES):
                user_name_map[user_idx] = COCO_NAMES[coco_idx]
            else:
                user_name_map[user_idx] = str(user_idx)
        openpose_skeleton_overlay._user_name_map = user_name_map
    else:
        openpose_skeleton_overlay._user_connections = None

    openpose_skeleton_overlay(args.input_video, csv_to_use, args.output_video, points_only=args.points_only)
