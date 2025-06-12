import torch
import cv2
import os
import sys
import numpy as np
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms
import torch.nn as nn

# 모델 구조 (CNN + GRU)
class CNN_GRU_Classifier(nn.Module):
    def __init__(self, hidden_size=128, num_layers=1):
        super().__init__()
        # CNN encoder
        self.cnn = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Flatten()
        )
        self.flattened_size = 32 * 56 * 56  # assuming input is 224x224
        self.gru = nn.GRU(input_size=self.flattened_size, hidden_size=hidden_size, num_layers=num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):  # x shape: (B, T, C, H, W)
        B, T, C, H, W = x.shape
        x = x.view(B * T, C, H, W)
        x = self.cnn(x)
        x = x.view(B, T, -1)  # reshape for GRU
        out, _ = self.gru(x)
        out = out[:, -1, :]  # 마지막 타임스텝 출력
        out = self.fc(out)
        return out

# 비디오 처리 함수
def process_video(video_path, model):
    # 비디오 로드 (OpenCV)
    cap = cv2.VideoCapture(video_path)
    frames = []

    while(cap.isOpened()):
        ret, frame = cap.read()
        if not ret:
            break

        # 이미지 전처리 (Resizing, Normalization)
        frame = cv2.resize(frame, (224, 224))  # 모델의 입력 크기에 맞게
        frame = frame.astype(np.float32) / 255.0  # Normalize [0, 1]
        frame = np.transpose(frame, (2, 0, 1))  # HWC -> CHW
        frames.append(frame)

    cap.release()

    # 리스트를 numpy 배열로 변환 후 tensor로 변환
    frames = np.array(frames)  # (T, C, H, W) 형태의 numpy 배열
    frames = torch.tensor(frames).unsqueeze(0)  # (1, T, C, H, W)

    # 모델 예측
    model.eval()
    with torch.no_grad():
        output = model(frames)
        prediction = torch.sigmoid(output).item()  # Sigmoid 활성화 함수를 통해 0~1 범위로 변환

    # 결과: 1은 "good", 0은 "bad"
    return 1 if prediction > 0.3 else 0

# 실행 (Spring에서 호출될 때 파일 경로 전달)
if __name__ == "__main__":
    video_dir = "E:/resVue/resPy/uploaded-videos"
    video_filename = sys.argv[1]  # Spring에서 비디오 파일 이름을 인자로 받음
    video_path = os.path.join(video_dir, video_filename)

    # CPU 장치 사용 강제
    device = torch.device('cpu')

    # 모델 로드
    model_path = "E:/resVue/resPy/cnn_gru_model.pth"
    model = CNN_GRU_Classifier()
    model.load_state_dict(torch.load(model_path, map_location=device))  # 모델을 CPU에 맞게 로드

    # 비디오 처리 및 예측
    result = process_video(video_path, model)
    print(result)  # 결과 출력 (Spring이 이 결과를 읽어들일 수 있도록)
