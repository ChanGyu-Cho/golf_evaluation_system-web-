"""
MLP 분류기 (stgcn 전용): stgcn 임베딩만 읽어 학습된 MLP 모델로 이진분류
mlp_predict(stgcn_npy, model_path=None, scaler_path=None) -> dict
 - stgcn_npy: path to numpy .npy file containing the stgcn embedding for one sample
 - model_path: path to a saved model state_dict (defaults to ./mlp_model.pth)
 - scaler_path: optional path to a saved StandardScaler (joblib). If not provided,
   no scaling is applied and a warning is logged.
"""
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
import logging
import sys

# joblib optional
try:
    from joblib import load as joblib_load
except Exception:
    joblib_load = None

# 모든 로그가 stdout으로 가도록 설정
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='[PYTHON-MLP] %(message)s')


def mlp_predict(stgcn_npy, model_path=None, scaler_path=None):
    """Predict using a trained MLP model and a single stgcn embedding file.
    Returns dict {prob_true, prob_false, pred} or error info on failure.
    """
    # Backward compatibility: some callers still call mlp_predict(timesformer_npy, stgcn_npy)
    # In that legacy call the second positional arg ends up in model_path here and
    # will typically be a .npy path. Detect that and shift variables so we use the
    # second positional arg as the stgcn input and keep model_path as default.
    if model_path and isinstance(model_path, str) and model_path.lower().endswith('.npy'):
        logging.info("Detected legacy mlp_predict(timesformer_npy, stgcn_npy) call - using second arg as stgcn file")
        stgcn_npy = model_path
        model_path = None

    model_path = model_path or "mlp_model.pth"
    try:
        # load stgcn embedding
        X_st = np.load(stgcn_npy)
        # flatten multi-d arrays to 1D feature vector
        if X_st.ndim > 1:
            X_st = X_st.flatten()
        X = X_st.reshape(1, -1).astype(np.float32)

        # scaling: try to load provided scaler, else warn and skip scaling
        if scaler_path and joblib_load:
            try:
                scaler = joblib_load(scaler_path)
                X_scaled = scaler.transform(X)
            except Exception as e:
                logging.warning(f"Failed to load/transform scaler from {scaler_path}: {e}; continuing without scaler")
                X_scaled = X
        else:
            if scaler_path and not joblib_load:
                logging.warning("joblib not available to load scaler; input will not be scaled.")
            else:
                # Use ASCII hyphen to avoid encoding problems in some consoles
                logging.info("No scaler_path provided - input will not be scaled.")
            X_scaled = X

        # define model architecture consistent with training head (input dim set from data)
        class HeadMLP(nn.Module):
            def __init__(self, in_dim):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(in_dim, 1024),
                    nn.BatchNorm1d(1024),
                    nn.ReLU(),
                    nn.Dropout(0.5),
                    nn.Linear(1024, 512),
                    nn.BatchNorm1d(512),
                    nn.ReLU(),
                    nn.Dropout(0.5),
                    nn.Linear(512, 256),
                    nn.BatchNorm1d(256),
                    nn.ReLU(),
                    nn.Dropout(0.5),
                    nn.Linear(256, 128),
                    nn.BatchNorm1d(128),
                    nn.ReLU(),
                    nn.Dropout(0.5),
                    nn.Linear(128, 2)
                )
            def forward(self, x):
                return self.net(x)

        DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = HeadMLP(X_scaled.shape[1]).to(DEVICE)

        # load saved state dict
        try:
            state = torch.load(model_path, map_location=DEVICE)
            if isinstance(state, dict) and 'state_dict' in state:
                model.load_state_dict(state['state_dict'])
            else:
                model.load_state_dict(state)
            logging.info(f"Loaded MLP model weights from {model_path}")
        except Exception as e:
            logging.error(f"Failed to load model from {model_path}: {e}")
            return {"prob_true": None, "prob_false": None, "pred": None, "error": f"model load failed: {e}"}

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
