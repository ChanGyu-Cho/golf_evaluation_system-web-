import cv2
import pandas as pd
import numpy as np
import json
from pathlib import Path

video = Path(r"d:/golf_evaluation_system-web-/resPy/crop_video/1_20201124_General_037_DOS_A_M40_MS_038_crop_crop.mp4")
csv = Path(r"d:/golf_evaluation_system-web-/resPy/crop_csv/1_20201124_General_037_DOS_A_M40_MS_038_crop_crop.csv")
out = Path(r"d:/golf_evaluation_system-web-/resPy/skeleton_video/diagnose_connections.png")

# canonical names and connections (should match openpose_skeleton_overlay)
COCO_NAMES = [
    "Nose", "LEye", "REye", "LEar", "REar", "LShoulder", "RShoulder",
    "LElbow", "RElbow", "LWrist", "RWrist", "LHip", "RHip", "LKnee",
    "RKnee", "LAnkle", "RAnkle"
]
COCO_CONNECTIONS = [
    (0,1),(0,2),(1,3),(2,4),
    (5,6),(5,7),(7,9),(6,8),(8,10),
    (5,11),(6,12),(11,12),
    (11,13),(13,15),(12,14),(14,16)
]

if not video.exists() or not csv.exists():
    print(json.dumps({"error":"missing_files", "video":str(video), "csv":str(csv)}))
    raise SystemExit(2)

df = pd.read_csv(str(csv))
# detect format
x_cols = [c for c in df.columns if c.endswith('_x')]
y_cols = [c for c in df.columns if c.endswith('_y')]
score_cols = [c for c in df.columns if c.endswith('_c') or c.endswith('_score') or c.startswith('score_')]

# determine normalized
def is_normalized(cols):
    try:
        vals = df[cols].replace([float('inf'), -float('inf')], np.nan).dropna(how='all')
        if vals.size==0:
            return False
        return float(vals.to_numpy(dtype=float).max()) <= 1.0
    except Exception:
        return False

normalized = is_normalized(x_cols) if x_cols else False

# find first non-empty row
first_idx = None
for i in range(len(df)):
    if x_cols:
        xv = df.loc[i, x_cols].astype(float).to_numpy()
        yv = df.loc[i, y_cols].astype(float).to_numpy()
        if np.nansum(xv) + np.nansum(yv) > 0:
            first_idx = i
            break

if first_idx is None:
    print(json.dumps({"error":"no_nonempty_row"}))
    raise SystemExit(3)

cap = cv2.VideoCapture(str(video))
ret, frame = cap.read()
cap.release()
if not ret:
    print(json.dumps({"error":"video_read_fail"}))
    raise SystemExit(4)

h, w = frame.shape[:2]

# build keypoints array in index order matching COCO_NAMES
keypoints = []
for name in COCO_NAMES:
    xv = df.at[first_idx, f"{name}_x"] if f"{name}_x" in df.columns else np.nan
    yv = df.at[first_idx, f"{name}_y"] if f"{name}_y" in df.columns else np.nan
    sc = df.at[first_idx, f"{name}_c"] if f"{name}_c" in df.columns else None
    if pd.isna(xv) or pd.isna(yv) or (sc is not None and not pd.isna(sc) and float(sc) <= 0.01) or (xv==0 and yv==0):
        keypoints.append([-1,-1])
        continue
    try:
        xv = float(xv); yv = float(yv)
    except Exception:
        keypoints.append([-1,-1]); continue
    if normalized:
        keypoints.append([xv * w, yv * h])
    else:
        keypoints.append([xv, yv])

kp = np.array(keypoints)

# draw points with labels (points-only)
img = frame.copy()
for i,(x,y) in enumerate(kp):
    if x<0 or y<0:
        continue
    # draw larger red dot only
    cv2.circle(img, (int(round(x)), int(round(y))), 8, (0,0,255), -1)

cv2.imwrite(str(out), img)

# print mapping and sample coords
report = {"first_row_index":int(first_idx), "normalized": bool(normalized), "frame_w":w, "frame_h":h, "keypoints_sample": {}} 
for i,name in enumerate(COCO_NAMES):
    x,y = kp[i]
    report[ i ] = {"name":name, "x": float(x) if x>=0 else None, "y": float(y) if y>=0 else None }

print(json.dumps(report, ensure_ascii=False, indent=2))
print('wrote', out)
