"""
OpenPose 실행, crop, csv 유틸리티
- run_openpose_and_crop: 비디오 1개에 대해 crop_video, crop_csv 생성
"""
import subprocess
from pathlib import Path
import shutil
import json
import numpy as np
import cv2
import os

def run_openpose_and_crop(input_video, crop_video_dir, crop_csv_dir, skeleton_video_dir):
    """
    input_video: Path
    crop_video_dir, crop_csv_dir: Path
    return: (crop_video_path, crop_csv_path)
    """
    # OpenPose 실행 경로 및 모델 경로 (COCO17)
    OPENPOSE_EXE = Path(r"C:/openpose/openpose/bin/OpenPoseDemo.exe")
    OPENPOSE_ROOT = OPENPOSE_EXE.parent.parent
    PAD_RATIO = 0.10
    basename = Path(input_video).stem
    # COCO17 모델 사용
    MODEL_FOLDER = OPENPOSE_ROOT / "models"
    COCO_MODEL = MODEL_FOLDER / "pose/coco/pose_iter_440000.caffemodel"
    assert COCO_MODEL.exists(), f"COCO 모델 파일이 존재하지 않습니다: {COCO_MODEL}"
    # tmp_json_dir을 resPy 폴더 내부에 생성
    respy_dir = Path(__file__).parent.resolve()
    tmp_json_dir = respy_dir / f"_tmp_json_{basename}"
    tmp_json_dir.mkdir(exist_ok=True, parents=True)
    # Prepare a robust cleanup helper and register it to run at process exit.
    import atexit, time
    keep_tmp = os.environ.get('KEEP_TMP_JSON', '0') == '1'
    def _rmtree_force(path):
        # onerror handler: try to fix permissions then retry
        def _onerror(func, path_, exc_info):
            try:
                os.chmod(path_, 0o700)
                func(path_)
            except Exception:
                pass
        try:
            shutil.rmtree(path, onerror=_onerror)
            return True
        except Exception:
            # retry a few times with small backoff
            for _ in range(3):
                time.sleep(0.2)
                try:
                    shutil.rmtree(path, onerror=_onerror)
                    return True
                except Exception:
                    continue
        return False

    def _cleanup_tmp():
        if keep_tmp:
            print(f"[DEBUG] KEEP_TMP_JSON=1, preserving tmp_json_dir: {tmp_json_dir}")
            return
        ok = _rmtree_force(tmp_json_dir)
        if not ok:
            print(f"[WARN] _rmtree_force failed to remove tmp_json_dir: {tmp_json_dir}")

    atexit.register(_cleanup_tmp)
    crop_video_dir = Path(crop_video_dir); crop_video_dir.mkdir(exist_ok=True)
    crop_csv_dir = Path(crop_csv_dir); crop_csv_dir.mkdir(exist_ok=True)
    # Prepare absolute input path and pre-reencode input video to ensure OpenPose/OpenCV can open it reliably
    abs_input_video = os.path.abspath(str(input_video))
    reencoded_video = tmp_json_dir / f"{basename}_reencoded.mp4"
    abs_reencoded = os.path.abspath(str(reencoded_video))
    if not reencoded_video.exists():
        ff_cmd = ["ffmpeg", "-y", "-i", abs_input_video, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", abs_reencoded]
        try:
            p = subprocess.run(ff_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if p.returncode != 0:
                raise RuntimeError(f"ffmpeg re-encode failed: returncode={p.returncode}\nstdout={p.stdout}\nstderr={p.stderr}")
        except Exception as e:
            raise RuntimeError(f"Pre-reencode failed: {e}")
    # use reencoded file as input for OpenPose
    abs_input_for_openpose = abs_reencoded

    # 1. OpenPose 원본 실행 (json 추출, COCO17)
    raw_json_dir = tmp_json_dir / f"raw_{basename}"
    raw_json_dir.mkdir(exist_ok=True)
    abs_raw_json_dir = os.path.abspath(str(raw_json_dir))
    cmd = [str(OPENPOSE_EXE),
        "--video", abs_input_for_openpose,
        "--write_json", abs_raw_json_dir,
        "--display", "0", "--render_pose", "0",
        "--number_people_max", "1",
        "--model_folder", str(MODEL_FOLDER),
        "--model_pose", "COCO"]
    # run with capture; retry once on failure
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=OPENPOSE_ROOT, text=True)
        if res.returncode != 0:
            # retry once
            res2 = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=OPENPOSE_ROOT, text=True)
            if res2.returncode != 0:
                raise RuntimeError(f"OpenPose failed: returncode={res2.returncode}\nstdout={res2.stdout}\nstderr={res2.stderr}")
    except Exception as e:
        raise RuntimeError(f"OpenPose execution error: {e}")

    # 2. 주요 인물 박스 추출 (DBSCAN)
    def main_person_boxes(json_dir):
        from sklearn.cluster import DBSCAN
        centers, boxes = [], []
        for jf in sorted(json_dir.glob("*.json")):
            data = json.load(open(jf))
            people = data.get("people")
            if not people:
                continue
            kps = np.array(people[0]["pose_keypoints_2d"]).reshape(-1, 3)  # COCO17: (17,3)
            if kps[11, 2] < 0.10:  # COCO: 11번이 MidHip(중심)
                continue
            cx, cy = kps[11, :2]
            valid = kps[:, 2] > 0.05
            xs, ys = kps[valid, 0], kps[valid, 1]
            centers.append([cx, cy])
            boxes.append([xs.min(), ys.min(), xs.max(), ys.max()])
        if not centers:
            return []
        centers = np.array(centers)
        labels = DBSCAN(eps=100, min_samples=5).fit_predict(centers)
        if (labels != -1).any():
            main_label = np.bincount(labels[labels != -1]).argmax()
        else:
            main_label = 0
        return [boxes[i] for i, lb in enumerate(labels) if lb == main_label]

    def union_box(box_list):
        arr = np.array(box_list)
        x1, y1 = arr[:, :2].min(0)
        x2, y2 = arr[:, 2:].max(0)
        w, h = x2 - x1, y2 - y1
        pad_w = w * PAD_RATIO
        pad_h = h * PAD_RATIO
        return int(x1 - pad_w), int(y1 - pad_h), int(w + 2 * pad_w), int(h + 2 * pad_h)

    # 3. crop bbox 계산
    boxes = main_person_boxes(raw_json_dir)
    if not boxes:
        raise RuntimeError(f"No valid person detected in {input_video}")
    bbox = union_box(boxes)

    # 4. crop_video 생성 (ffmpeg)
    crop_video_path = crop_video_dir / f"{basename}_crop.mp4"
    x, y, w, h = bbox
    cap = cv2.VideoCapture(str(input_video))
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    if x < 0: x = 0
    if y < 0: y = 0
    if x + w > orig_w: w = orig_w - x
    if y + h > orig_h: h = orig_h - y
    if w <= 0 or h <= 0:
        raise ValueError(f"Invalid crop size: {(w, h)} for video {input_video}")
    abs_crop_video_path = os.path.abspath(str(crop_video_path))
    cmd = ["ffmpeg", "-y", "-i", abs_input_video,
        "-filter:v", f"crop={w}:{h}:{x}:{y}",
        "-pix_fmt", "yuv420p", abs_crop_video_path]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # 5. crop_video에 대해 openpose 재실행 (crop_json, COCO17)
    crop_json_dir = tmp_json_dir / f"crop_{basename}"
    crop_json_dir.mkdir(exist_ok=True)
    abs_crop_json_dir = os.path.abspath(str(crop_json_dir))
    cmd = [str(OPENPOSE_EXE),
        "--video", abs_crop_video_path,
        "--write_json", abs_crop_json_dir,
        "--display", "0", "--render_pose", "0",
        "--number_people_max", "1",
        "--model_folder", str(MODEL_FOLDER),
        "--model_pose", "COCO"]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=OPENPOSE_ROOT, text=True)
        if res.returncode != 0:
            res2 = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=OPENPOSE_ROOT, text=True)
            if res2.returncode != 0:
                raise RuntimeError(f"OpenPose (crop) failed: returncode={res2.returncode}\nstdout={res2.stdout}\nstderr={res2.stderr}")
    except Exception as e:
        raise RuntimeError(f"OpenPose (crop) execution error: {e}")

    # 6. crop_json → crop_csv
    # COCO17 keypoint 이름
    KP = [
        "Nose", "LEye", "REye", "LEar", "REar", "LShoulder", "RShoulder", "LElbow", "RElbow",
        "LWrist", "RWrist", "LHip", "RHip", "LKnee", "RKnee", "LAnkle", "RAnkle"
    ]
    COLS = [f"{n}_{a}" for n in KP for a in ("x","y","c")]
    crop_csv_path = crop_csv_dir / f"{basename}_crop.csv"
    rows = []
    for jf in sorted(crop_json_dir.glob("*.json")):
        data = json.load(open(jf))
        people = data.get("people")
        if not people:
            rows.append([np.nan] * len(COLS))
        else:
            kps = np.array(people[0]["pose_keypoints_2d"]).reshape(-1, 3)
            kps = kps[:17]  # COCO17 keypoint만 사용
            rows.append(kps.flatten())
    import pandas as pd
    pd.DataFrame(rows, columns=COLS).to_csv(crop_csv_path, index=False)

    # 7. 임시 폴더 정리: 즉시 제거 시도 (또는 atexit에 의해 프로세스 종료 시 시도)
    try:
        if not keep_tmp:
            ok = _rmtree_force(tmp_json_dir)
            if not ok:
                print(f"[WARN] Immediate removal failed for tmp_json_dir {tmp_json_dir}; will attempt again at process exit.")
        else:
            print(f"[DEBUG] KEEP_TMP_JSON=1, preserving tmp_json_dir: {tmp_json_dir}")
    except Exception as e:
        print(f"[WARN] Failed to remove tmp_json_dir {tmp_json_dir}: {e}")
    return crop_video_path, crop_csv_path

# --- skeleton 비디오 생성 함수 ---
