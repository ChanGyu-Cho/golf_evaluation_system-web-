import cv2
import pandas as pd
import numpy as np
from pathlib import Path

video = Path(r"d:/golf_evaluation_system-web-/resPy/crop_video/1_20201124_General_037_DOS_A_M40_MS_038_crop_crop.mp4")
csv = Path(r"d:/golf_evaluation_system-web-/resPy/crop_csv/1_20201124_General_037_DOS_A_M40_MS_038_crop_crop.csv")
out = Path(r"d:/golf_evaluation_system-web-/resPy/skeleton_video/test_overlay_points.png")

if not video.exists() or not csv.exists():
    print('missing source files')
    raise SystemExit(2)

df = pd.read_csv(str(csv))
# find first non-empty row
x_cols = [c for c in df.columns if c.endswith('_x')]
y_cols = [c for c in df.columns if c.endswith('_y')]
first_idx = None
for i in range(len(df)):
    xv = df.loc[i, x_cols].astype(float).to_numpy()
    yv = df.loc[i, y_cols].astype(float).to_numpy()
    if np.nansum(xv) + np.nansum(yv) > 0:
        first_idx = i
        break
if first_idx is None:
    print('no nonempty rows')
    raise SystemExit(3)

cap = cv2.VideoCapture(str(video))
ret, frame = cap.read()
cap.release()
if not ret:
    print('failed to read frame')
    raise SystemExit(4)

h, w = frame.shape[:2]
# assume CSV is in pixels (based on previous check)
xv = df.loc[first_idx, x_cols].astype(float).to_numpy()
yv = df.loc[first_idx, y_cols].astype(float).to_numpy()

# draw points and labels
for k, (x, y) in enumerate(zip(xv, yv)):
    if np.isnan(x) or np.isnan(y) or (x==0 and y==0):
        continue
    cx = int(round(x))
    cy = int(round(y))
    cv2.circle(frame, (cx, cy), 4, (0,0,255), -1)
    cv2.putText(frame, str(k), (cx+5, cy-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,255,0), 1)

cv2.imwrite(str(out), frame)
print('wrote', out)
