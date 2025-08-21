# ======================[ IMPORTS & ENV ]======================
import os
import sys
import traceback
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import pickle
from mmengine.config import Config
from mmengine.runner import Runner, load_checkpoint

# print('[STEP] STGCN embedding script start'); sys.stdout.flush()

# ======================[ MAIN FUNCTION ]======================
def extract_stgcn_embedding(crop_csv_path, out_npy_path):
    """
    crop_csv_path: Path
    out_npy_path: Path (저장)
    """
    # 환경에 맞게 경로 수정
    BASE_DIR = r"D:/mmaction2"
    sys.path.insert(0, BASE_DIR)
    CFG = r"D:/golf_evaluation_system-web-/resPy/my_stgcnpp.py"
    CKPT = r"D:/golf_evaluation_system-web-/resPy/stgcn_62p.pth"
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

    # data_loader.ipynb의 make_pkl, load_and_process 방식 반영
    def csv_to_pkl(csv_path, out_pkl):
        import pandas as pd
        df = pd.read_csv(csv_path)
        F = df.shape[0]
        V = 17
        COCO_NAMES = [
            "Nose", "LEye", "REye", "LEar", "REar", "LShoulder", "RShoulder", "LElbow", "RElbow",
            "LWrist", "RWrist", "LHip", "RHip", "LKnee", "RKnee", "LAnkle", "RAnkle"
        ]
        # x_0~x_16 포맷
        x_cols = [f"x_{i}" for i in range(V)]
        y_cols = [f"y_{i}" for i in range(V)]
        score_cols = [f"score_{i}" for i in range(V)]
        if all(col in df.columns for col in x_cols) and all(col in df.columns for col in y_cols) and all(col in df.columns for col in score_cols):
            arr = np.stack([
                np.stack([df[x_cols].values, df[y_cols].values, df[score_cols].values], axis=2)
            ], axis=0)[0]
        # COCO 관절명 기반 포맷 (Nose_x, ...)
        elif all(f"{name}_x" in df.columns for name in COCO_NAMES) and all(f"{name}_y" in df.columns for name in COCO_NAMES) and all(f"{name}_c" in df.columns for name in COCO_NAMES):
            arr = np.stack([
                np.stack([
                    df[[f"{name}_x" for name in COCO_NAMES]].values,
                    df[[f"{name}_y" for name in COCO_NAMES]].values,
                    df[[f"{name}_c" for name in COCO_NAMES]].values
                ], axis=2)
            ], axis=0)[0]
        else:
            raise ValueError("CSV는 반드시 openpose COCO17 포맷(x_0~x_16, y_0~x_16, score_0~16) 또는 (Nose_x, ..., RAnkle_c) 포맷이어야 합니다.")
        # (F, 17, 3)
        keypoint = arr[:, :, :2]  # (F, 17, 2)
        keypoint_score = arr[:, :, 2]  # (F, 17)
        keypoint = np.expand_dims(keypoint, axis=0)  # (1, F, 17, 2)
        keypoint_score = np.expand_dims(keypoint_score, axis=0)  # (1, F, 17)
        ann = {
            'frame_dir': csv_path.stem,
            'total_frames': F,
            'keypoint': keypoint,
            'keypoint_score': keypoint_score,
            'label': 0,
            'img_shape': (1080, 1920),
            'original_shape': (1080, 1920),
            'metainfo': {'frame_dir': csv_path.stem, 'img_shape': (1080, 1920)}
        }
        data = {
            'annotations': [ann],
            'split': {'xsub_val': [csv_path.stem]}
        }
        with open(out_pkl, 'wb') as f:
            pickle.dump(data, f, protocol=4)

    tmp_pkl = Path(str(out_npy_path).replace('.npy', '.pkl'))
    csv_to_pkl(crop_csv_path, tmp_pkl)

    # runner, model, last_lin, feat_dim 정의
    cfg = Config.fromfile(CFG)
    # ann_file 경로를 임시 pkl로 덮어쓰기
    if hasattr(cfg, 'test_dataloader'):
        cfg.test_dataloader.dataset.ann_file = str(tmp_pkl)
    else:
        cfg.data.test.dataset.ann_file = str(tmp_pkl)
    runner = Runner.from_cfg(cfg)
    runner.load_checkpoint(CKPT, map_location=DEVICE)
    model = runner.model
    model = model.to(DEVICE)
    model.eval()
    # 마지막 Linear layer 찾기 (cls_head 내부에서 nn.Linear 탐색)
    last_lin = next((m for m in model.cls_head.modules() if isinstance(m, nn.Linear)), None)
    if last_lin is None:
        raise RuntimeError("cls_head 내부에 nn.Linear 레이어가 없습니다.")
    feat_dim = last_lin.in_features

    embs = []
    with torch.no_grad():
        for batch in runner.test_dataloader:
            data_samples = batch['data_samples']
            inputs = batch['inputs']
            for i, ds in enumerate(data_samples):
                clip_embs = []
                def hook(m, inp, out):
                    clip_embs.append(inp[0].cpu().squeeze(0))
                handle = last_lin.register_forward_hook(hook)
                if isinstance(inputs, list):
                    inp = inputs[i].unsqueeze(0).to(DEVICE)
                elif isinstance(inputs, dict):
                    inp = {k: v[i].unsqueeze(0).to(DEVICE) for k, v in inputs.items()}
                elif torch.is_tensor(inputs):
                    inp = inputs[i].unsqueeze(0).to(DEVICE)
                model.forward(inp, [ds], mode='predict')
                handle.remove()
                if not clip_embs:
                    clip_embs.append(torch.zeros(feat_dim))
                video_emb = torch.stack(clip_embs, 0).mean(0).cpu().numpy()
                video_emb = np.nan_to_num(video_emb, nan=0.0, posinf=0.0, neginf=0.0)
                embs.append(video_emb)
    em_arr = np.stack(embs, 0)
    np.save(out_npy_path, em_arr[0])
    tmp_pkl.unlink()  # 임시 pkl 삭제

    # print(f'[SUCCESS] Saved embedding to {out_npy_path}'); sys.stdout.flush()

# ======================[ ENTRY POINT ]======================
if __name__ == "__main__":
    try:
        if len(sys.argv) != 3:
            print("Usage: python extract_stgcn_single.py <input_csv> <output_npy>", file=sys.stderr)
            sys.exit(1)
        input_csv = sys.argv[1]
        output_npy = sys.argv[2]
        extract_stgcn_embedding(Path(input_csv), Path(output_npy))
        # print(f"[STGCN] Saved embedding to {output_npy}")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f'[FAIL] STGCN embedding failed: error={e}', file=sys.stderr); sys.stderr.flush()
        print(tb, file=sys.stderr); sys.stderr.flush()
        sys.exit(1)
