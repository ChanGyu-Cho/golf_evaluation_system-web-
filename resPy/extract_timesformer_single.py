
"""
단일 crop_video에서 Timesformer 임베딩 추출
- extract_timesformer_embedding: crop_video_path, out_npy_path
"""
from pathlib import Path
import torch
import torch.nn as nn
import numpy as np
from torchvision import transforms
from torchvision.transforms import InterpolationMode
from decord import VideoReader
import sys

def extract_timesformer_embedding(crop_video_path, out_npy_path):
    """
    crop_video_path: Path
    out_npy_path: Path (저장)
    """
    # 환경에 맞게 경로 수정
    MODEL_PATH = Path(__file__).parent / 'timesformer_model.pth'
    PRETRAINED = Path(r'D:/timesformer/pretrained/TimeSformer_divST_96x4_224_K600.pyth')
    IMG_SIZE = 224
    NUM_FRAMES = 96
    CLIPS_PER_VID = 2
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
    sys.path.append(r'D:/timesformer')
    from timesformer.models.vit import TimeSformer
    mean = [0.485, 0.456, 0.406]
    std  = [0.229, 0.224, 0.225]
    eval_transform = transforms.Compose([
        transforms.Resize(256, interpolation=InterpolationMode.BICUBIC),
        transforms.CenterCrop(IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])
    def uniform_sample(length, num):
        if length >= num:
            return np.linspace(0, length-1, num, dtype=int)
        return np.pad(np.arange(length), (0,num-length), mode='edge')
    def load_clip(path):
        vr = VideoReader(str(path))
        L  = len(vr)
        segs = np.linspace(0, L, CLIPS_PER_VID+1, dtype=int)
        clips = []
        for s,e in zip(segs[:-1], segs[1:]):
            idx = uniform_sample(e-s, NUM_FRAMES) + s
            arr = vr.get_batch(idx).asnumpy()
            proc = []
            for frame in arr:
                img = transforms.ToPILImage()(frame)
                img_t = eval_transform(img)
                proc.append(img_t)
            clip = torch.stack(proc, dim=1)
            clips.append(clip)
        return clips
    class TimeSformerEmbed(nn.Module):
        def __init__(self, model_path, img_size, num_frames, num_classes, pretrained_path):
            super().__init__()
            self.base = TimeSformer(
                img_size=img_size,
                num_frames=num_frames,
                num_classes=num_classes,
                attention_type='divided_space_time',
                pretrained_model=str(pretrained_path)
            )
            ckpt = torch.load(model_path, map_location="cpu", weights_only=False)
            # state_dict key 자동 맞춤
            if "model" in ckpt:
                state = ckpt["model"]
            elif "base" in ckpt:
                state = ckpt["base"]
            else:
                state = ckpt
            # key가 'base.model.xxx'처럼 한 번 더 감싸져 있으면 prefix 제거
            if any(k.startswith("base.model.") for k in state.keys()):
                new_state = {}
                for k, v in state.items():
                    if k.startswith("base.model."):
                        new_state[k[len("base.model."):]] = v
                    else:
                        new_state[k] = v
                state = new_state
            self.base.load_state_dict(state, strict=False)
            self.base.head = nn.Identity()
            self.base.cls_head = nn.Identity()
        def forward(self, x):
            return self.base(x)
    embed_model = TimeSformerEmbed(
        model_path=MODEL_PATH,
        img_size=IMG_SIZE,
        num_frames=NUM_FRAMES,
        num_classes=2,
        pretrained_path=PRETRAINED
    ).to(DEVICE)
    embed_model.eval()
    clips = load_clip(crop_video_path)
    feats = []
    for clip in clips:
        c = clip.unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            out = embed_model.base.model.forward_features(c)
        cls = out[:,0,:] if out.ndim==3 else out
        feats.append(cls.squeeze(0).cpu().numpy())
    emb = np.stack(feats,0).mean(0)
    np.save(out_npy_path, emb)

if __name__ == "__main__":
    import sys
    import traceback
    from pathlib import Path
    try:
        if len(sys.argv) != 3:
            print("Usage: python extract_timesformer_single.py <input_video> <output_npy>")
            sys.exit(1)
        input_video = sys.argv[1]
        output_npy = sys.argv[2]
        extract_timesformer_embedding(Path(input_video), Path(output_npy))
        print(f"Saved embedding to {output_npy}")
    except Exception as e:
        print("[ERROR] Exception in extract_timesformer_single.py:")
        traceback.print_exc()
        sys.exit(1)
