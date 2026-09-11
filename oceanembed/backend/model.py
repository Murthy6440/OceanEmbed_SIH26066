"""
OceanEmbed SIH26066 - Lightweight PyTorch subsurface estimation model
Trained on REAL Argo float data (5 features: surface_temp, surface_sal,
depth, lat_norm, lon_norm) -> predicts (temperature, salinity) at depth.
"""
import json
import os

import numpy as np
import torch
import torch.nn as nn

FEATURE_NAMES = ["surface_temp", "surface_sal", "depth", "lat_norm", "lon_norm"]
TARGET_NAMES = ["temperature", "salinity"]

INPUT_DIM = len(FEATURE_NAMES)   # 5
OUTPUT_DIM = len(TARGET_NAMES)   # 2

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_model")
MODEL_PATH = os.path.join(MODEL_DIR, "oceanembed_model.pt")
X_SCALER_PATH = os.path.join(MODEL_DIR, "scaler_x.json")
Y_SCALER_PATH = os.path.join(MODEL_DIR, "scaler_y.json")
METRICS_PATH = os.path.join(MODEL_DIR, "validation_metrics.json")


class OceanNetCNNLSTM(nn.Module):
    def __init__(self, input_dim=INPUT_DIM, output_dim=OUTPUT_DIM):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(input_dim, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
        )
        self.lstm = nn.LSTM(input_size=32, hidden_size=32, batch_first=True)
        self.head = nn.Sequential(
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Dropout(0.05),
            nn.Linear(64, output_dim),
        )

    def forward(self, x):
        if not isinstance(x, torch.Tensor):
            x = torch.as_tensor(x, dtype=torch.float32)
        else:
            x = x.to(dtype=torch.float32)

        if x.dim() == 2:
            x = x.unsqueeze(1).transpose(1, 2)  # (B, input_dim, 1)
        elif x.dim() == 3 and x.shape[-1] == INPUT_DIM:
            x = x.transpose(1, 2)  # (B, input_dim, seq_len)

        x = self.conv(x)
        x = x.transpose(1, 2)  # (B, seq_len, 32)
        out, _ = self.lstm(x)
        x = out[:, -1, :]
        return self.head(x)


OceanNet = OceanNetCNNLSTM


class Scaler:
    def __init__(self, mean=None, std=None):
        self.mean = mean
        self.std = std

    def fit(self, X):
        self.mean = X.mean(axis=0)
        self.std = X.std(axis=0)
        self.std[self.std == 0] = 1.0
        return self

    def transform(self, X):
        return ((X - self.mean) / self.std).astype(np.float32)

    def inverse_transform(self, X):
        return X * self.std + self.mean

    def save(self, path):
        with open(path, "w") as f:
            json.dump({"mean": self.mean.tolist(), "std": self.std.tolist()}, f)

    @classmethod
    def load(cls, path):
        with open(path) as f:
            d = json.load(f)
        return cls(mean=np.array(d["mean"], dtype=np.float32),
                    std=np.array(d["std"], dtype=np.float32))


class OceanEmbedPredictor:
    def __init__(self):
        self.model = OceanNet()
        self.x_scaler = None
        self.y_scaler = None
        self.metrics = None
        self.loaded = False

    def load(self):
        try:
            state_dict = torch.load(MODEL_PATH, map_location="cpu")
            self.model.load_state_dict(state_dict)
        except RuntimeError:
            import train_model
            train_model.main()
            state_dict = torch.load(MODEL_PATH, map_location="cpu")
            self.model.load_state_dict(state_dict)

        self.model.eval()
        self.x_scaler = Scaler.load(X_SCALER_PATH)
        self.y_scaler = Scaler.load(Y_SCALER_PATH)
        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH) as f:
                self.metrics = json.load(f)
        self.loaded = True
        return self

    def predict(self, feature_vectors: np.ndarray) -> np.ndarray:
        if not self.loaded:
            raise RuntimeError("Model not loaded. Call .load() first (or run train_model.py).")
        feature_vectors = np.atleast_2d(feature_vectors).astype(np.float32)
        Xs = self.x_scaler.transform(feature_vectors)
        with torch.no_grad():
            out = self.model(torch.from_numpy(Xs)).numpy()
        return self.y_scaler.inverse_transform(out)