# ======================= TimeSformer 기반 비디오 분류 =======================
import os
import sys
import warnings
import torch
import cv2
import numpy as np
from pathlib import Path
import torch.nn as nn

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
warnings.filterwarnings("ignore")

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    
# TimeSformer import (timesformer 설치 경로가 sys.path에 포함되어야 함)
sys.path.append(r"D:/timesformer")
from timesformer.models.vit import TimeSformer

# 하이퍼파라미터 및 경로
IMG_SIZE = 224
NUM_FRAMES = 16
EVAL_CLIPS_PER_VIDEO = 4
MODEL_PATH = r"D:\golf_evaluation_system-web-\resPy\model.pth"
PRETRAIN_PTH = Path(r"D:/timesformer/pretrained/TimeSformer_divST_8x32_224_K600.pyth")



def uniform_sample(L, N):
    if L >= N:
        return np.linspace(0, L-1, N).astype(int)
    return np.pad(np.arange(L), (0, N-L), mode='edge')

def eval_clip(frames):
    import torchvision.transforms.functional as TF
    from torchvision.transforms import InterpolationMode
    out = []
    for f in frames:
        img = TF.to_pil_image(f)
        img = TF.resize(img, 256, interpolation=InterpolationMode.BICUBIC)
        img = TF.center_crop(img, IMG_SIZE)
        t = TF.to_tensor(img)
        t = TF.normalize(t, [0.45]*3, [0.225]*3)
        out.append(t)
    return torch.stack(out)

def load_clip(path, num_clips=EVAL_CLIPS_PER_VIDEO):
    from decord import VideoReader
    vr = VideoReader(str(path))
    L = len(vr)
    if L == 0:
        raise RuntimeError(f"[경고] 프레임이 0인 비디오: {path}")
    seg_edges = np.linspace(0, L, num_clips + 1, dtype=int)
    clips = []
    for s0, s1 in zip(seg_edges[:-1], seg_edges[1:]):
        idx = uniform_sample(s1 - s0, NUM_FRAMES) + s0
        arr = vr.get_batch(idx).asnumpy().astype(np.uint8)
        clip = torch.from_numpy(arr).permute(0, 3, 1, 2).contiguous()
        proc = eval_clip(clip)
        clips.append(proc.permute(1, 0, 2, 3))  # (C, T, H, W)
    return torch.stack(clips)  # (num_clips, C, T, H, W)

def process_video_timesformer(video_path, model, device):
    # 비디오에서 clip 추출 (평가용)
    clips = load_clip(video_path, num_clips=EVAL_CLIPS_PER_VIDEO)
    clips = clips.to(device)  # (num_clips, C, T, H, W)
    model.eval()
    with torch.no_grad():
        outs = model(clips)
        # 여러 클립의 로짓 평균
        logits = outs.view(EVAL_CLIPS_PER_VIDEO, -1).mean(dim=0)
        prob = torch.softmax(logits, dim=0)[1].item()  # 1(class True) 확률
    return 1 if prob > 0.5 else 0



if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            raise RuntimeError("Usage: python classify_video.py <video_filename>")

        video_dir = "D:/golf_evaluation_system-web-/resPy/uploaded-videos"
        video_filename = sys.argv[1]
        video_path = os.path.join(video_dir, video_filename)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # TimeSformer 모델 로드
        model = TimeSformer(
            img_size=IMG_SIZE, num_frames=NUM_FRAMES, num_classes=2,
            attention_type='divided_space_time',
            pretrained_model=str(PRETRAIN_PTH)
        ).to(device)
        # 파인튜닝된 가중치 로드
        state = torch.load(MODEL_PATH, map_location=device)
        if 'model' in state:
            state_dict = state['model']
        else:
            state_dict = state

        # 키 변환: 'base.model.' → ''
        new_state_dict = {}
        for k, v in state_dict.items():
            if k.startswith('base.model.'):
                new_state_dict[k.replace('base.model.', '')] = v
            elif k.startswith('base.'):
                new_state_dict[k.replace('base.', '')] = v
            else:
                new_state_dict[k] = v

        model.load_state_dict(new_state_dict, strict=False)

        # 예측
        result = process_video_timesformer(video_path, model, device)
        print(f"RESULT: {result}", flush=True)

    except Exception as ex:
        eprint(f"[ERROR] {ex}")
        sys.exit(2)
