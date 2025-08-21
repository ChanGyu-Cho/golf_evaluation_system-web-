import cv2
import pandas as pd
import numpy as np
import json
import sys
from pathlib import Path

video = Path(r"d:/golf_evaluation_system-web-/resPy/crop_video/1_20201124_General_037_DOS_A_M40_MS_038_crop_crop.mp4")
csv = Path(r"d:/golf_evaluation_system-web-/resPy/crop_csv/1_20201124_General_037_DOS_A_M40_MS_038_crop_crop.csv")

if not video.exists():
    print(json.dumps({"error":"video_not_found", "video": str(video)}))
    sys.exit(2)
if not csv.exists():
    print(json.dumps({"error":"csv_not_found", "csv": str(csv)}))
    sys.exit(2)

cap = cv2.VideoCapture(str(video))
if not cap.isOpened():
    print(json.dumps({"error":"video_open_failed", "video": str(video)}))
    sys.exit(3)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
cap.release()

df = pd.read_csv(str(csv))
# find x/y columns
x_cols = [c for c in df.columns if c.endswith('_x')]
y_cols = [c for c in df.columns if c.endswith('_y')]
report = {"video": str(video), "csv": str(csv), "frame_width": width, "frame_height": height, "x_cols": len(x_cols), "y_cols": len(y_cols)}

if not x_cols or not y_cols:
    report["error"] = "no_xy_columns"
    print(json.dumps(report, ensure_ascii=False))
    sys.exit(0)

# convert to numeric
xvals = df[x_cols].replace([np.inf, -np.inf], np.nan).astype(float).to_numpy()
yvals = df[y_cols].replace([np.inf, -np.inf], np.nan).astype(float).to_numpy()

report["x_min"] = float(np.nanmin(xvals))
report["x_max"] = float(np.nanmax(xvals))
report["y_min"] = float(np.nanmin(yvals))
report["y_max"] = float(np.nanmax(yvals))

# rows where all x,y in [0,1]
rows_norm = np.all((xvals >= 0.0) & (xvals <= 1.0) & (yvals >= 0.0) & (yvals <= 1.0), axis=1)
report["rows_all_normalized"] = int(rows_norm.sum())
report["rows_total"] = int(len(rows_norm))
report["percent_all_normalized"] = float(rows_norm.sum()) / max(1, len(rows_norm))

# rows with any x outside [0,width] or y outside [0,height]
out_x_row = np.any((xvals < 0.0) | (xvals > width), axis=1)
out_y_row = np.any((yvals < 0.0) | (yvals > height), axis=1)
report["rows_out_of_bounds_x"] = int(np.sum(out_x_row))
report["rows_out_of_bounds_y"] = int(np.sum(out_y_row))

# percentage of rows with many zeros (likely missing detection)
zero_rows = np.all((np.nan_to_num(xvals) == 0.0) & (np.nan_to_num(yvals) == 0.0), axis=1)
report["rows_all_zero"] = int(np.sum(zero_rows))

# sample first non-empty row index and its first 5 x/y values
nonempty_idx = None
for i in range(len(xvals)):
    if np.nansum(xvals[i]) + np.nansum(yvals[i]) > 0:
        nonempty_idx = i
        break
if nonempty_idx is not None:
    report["first_nonempty_row_index"] = int(nonempty_idx)
    report["first_nonempty_x_sample"] = [float(x) for x in xvals[nonempty_idx,:5]]
    report["first_nonempty_y_sample"] = [float(y) for y in yvals[nonempty_idx,:5]]
else:
    report["first_nonempty_row_index"] = None

print(json.dumps(report, ensure_ascii=False, indent=2))
