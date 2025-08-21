import pandas as pd
import numpy as np
import math

CSV = r"d:\golf_evaluation_system-web-\resPy\crop_csv\1_20201124_General_037_DOS_A_M40_MS_038_crop_1_crop.csv"

def calculate_angle_2d(joint_coords):
    AB = (joint_coords[0][0] - joint_coords[1][0], joint_coords[0][1] - joint_coords[1][1])
    BC = (joint_coords[2][0] - joint_coords[1][0], joint_coords[2][1] - joint_coords[1][1])
    dot_product = AB[0] * BC[0] + AB[1] * BC[1]
    magnitude_AB = math.sqrt(AB[0]**2 + AB[1]**2)
    magnitude_BC = math.sqrt(BC[0]**2 + BC[1]**2)
    if magnitude_AB * magnitude_BC == 0:
        return None
    cos_theta = dot_product / (magnitude_AB * magnitude_BC)
    cos_theta = max(min(cos_theta,1.0),-1.0)
    angle_radians = math.acos(cos_theta)
    return math.degrees(angle_radians)

COCO_KP = [
    "Nose", "LEye", "REye", "LEar", "REar", "LShoulder", "RShoulder", "LElbow", "RElbow",
    "LWrist", "RWrist", "LHip", "RHip", "LKnee", "RKnee", "LAnkle", "RAnkle"
]

print('reading', CSV)
df = pd.read_csv(CSV)
cols = set(df.columns)
use_name_cols = any(f"{name}_x" in cols for name in COCO_KP)
print('use_name_cols =', use_name_cols)

if use_name_cols:
    def get2d(row, j):
        x = row.get(f"{j}_x", np.nan)
        y = row.get(f"{j}_y", np.nan)
        try:
            return float(x), float(y)
        except Exception:
            return np.nan, np.nan
else:
    idx_map = {name:i for i,name in enumerate(COCO_KP)}
    def get2d(row, j):
        i = idx_map[j]
        x = row.get(f"x_{i}", np.nan)
        y = row.get(f"y_{i}", np.nan)
        try:
            return float(x), float(y)
        except Exception:
            return np.nan, np.nan

for i, row in df.head(20).iterrows():
    ls = get2d(row, 'LShoulder')
    le = get2d(row, 'LElbow')
    lw = get2d(row, 'LWrist')
    rs = get2d(row, 'RShoulder')
    re = get2d(row, 'RElbow')
    rw = get2d(row, 'RWrist')
    print(f'frame {i}: LShoulder={ls} LElbow={le} LWrist={lw}')
    a = calculate_angle_2d([ls, le, lw])
    b = calculate_angle_2d([rs, re, rw])
    print('  left_elbow=', a, ' right_elbow=', b)
