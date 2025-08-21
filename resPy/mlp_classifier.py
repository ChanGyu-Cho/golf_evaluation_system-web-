"""
MLP 분류기: timesformer/stgcn 임베딩 2개를 받아 이진분류
- mlp_predict(timesformer_npy, stgcn_npy) -> dict
"""
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
import logging
import sys

# 모든 로그가 stdout으로 가도록 설정
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='[PYTHON-MLP] %(message)s')

def mlp_predict(timesformer_npy, stgcn_npy):
    try:
        X_ts = np.load(timesformer_npy)
        X_st = np.load(stgcn_npy)
        if X_ts.ndim > 1:
            X_ts = X_ts.flatten()
        if X_st.ndim > 1:
            X_st = X_st.flatten()
        X = np.concatenate([X_ts, X_st], axis=0).reshape(1, -1).astype(np.float32)
        # 임의의 scaler (실제 학습된 scaler로 교체 필요)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        class HeadMLP(nn.Module):
            def __init__(self, in_dim):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(in_dim, 256),
                    nn.BatchNorm1d(256),
                    nn.ReLU(),
                    nn.Dropout(0.5),
                    nn.Linear(256, 2)
                )
            def forward(self, x):
                return self.net(x)
        DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = HeadMLP(X_scaled.shape[1]).to(DEVICE)
        # 실제 학습된 모델 파라미터를 불러와야 함 (여기선 임시 랜덤)
        model.eval()
        with torch.no_grad():
            logits = model(torch.from_numpy(X_scaled).to(DEVICE))
            probs = torch.softmax(logits, 1).cpu().numpy()[0]
            pred = int(probs[1] > 0.5)
        logging.info(f"MLP prob_true={probs[1]:.4f}, prob_false={probs[0]:.4f}, pred={pred}")
        return {"prob_true": float(probs[1]), "prob_false": float(probs[0]), "pred": pred}
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logging.error(f"MLP ERROR: {e}")
        print(tb, file=sys.stderr)
        return {"prob_true": None, "prob_false": None, "pred": None, "error": str(e)}
