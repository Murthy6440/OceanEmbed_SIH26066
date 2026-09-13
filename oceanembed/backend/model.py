"""
OceanEmbed SIH26066 - Hybrid PyTorch subsurface estimation model.
The architecture keeps the original ConvLSTM core and adds graph-style,
linear, and ViT-style branches for richer feature interaction while preserving
compatibility with the saved model and API contract.
"""
import json
import math
import os

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

FEATURE_NAMES = [
    "sst",
    "sss",
    "ssh",
    "u_curr",
    "v_curr",
    "u_wind",
    "v_wind",
    "depth",
    "lat_norm",
    "lon_norm",
]
TARGET_NAMES = ["temperature", "salinity"]

# Temporary fallback: many parts of the codebase and existing saved data
# still use the original 5-feature vector (surface_temp, surface_sal, depth,
# lat_norm, lon_norm). Use INPUT_DIM=5 for now to avoid startup/runtime
# mismatches (conv1d channel errors) until the dataset and training pipeline
# are migrated to the 10-feature satellite inputs.
INPUT_DIM = 5
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

        # Hybrid branches: keep the original ConvLSTM path and add GNN/linear/ViT
        # variants for richer spatial and feature interaction modeling.
        self.gnn = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, output_dim),
        )
        self.lnn = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, output_dim),
        )

        self.vit_patch_size = 2
        self.vit_embed_dim = 16
        self.vit_num_heads = 4
        self.vit = nn.ModuleDict({
            "patch_proj": nn.Linear(self.vit_patch_size, self.vit_embed_dim),
            "attn": nn.MultiheadAttention(
                embed_dim=self.vit_embed_dim,
                num_heads=self.vit_num_heads,
                batch_first=True,
                dropout=0.0,
            ),
            "norm": nn.LayerNorm(self.vit_embed_dim),
            "head": nn.Sequential(
                nn.Linear(self.vit_embed_dim, 32),
                nn.ReLU(),
                nn.Linear(32, output_dim),
            ),
        })
        self.vit_pos_embed = nn.Parameter(torch.zeros(1, 32, self.vit_embed_dim))
        self.vit_patch_proj = self.vit["patch_proj"]
        self.vit_attn = self.vit["attn"]
        self.vit_norm = self.vit["norm"]
        self.vit_head = self.vit["head"]

    def forward(self, x):
        if not isinstance(x, torch.Tensor):
            x = torch.as_tensor(x, dtype=torch.float32)
        else:
            x = x.to(dtype=torch.float32)

        x_flat = x
        if x.dim() == 2:
            x = x.unsqueeze(1).transpose(1, 2)  # (B, input_dim, 1)
        elif x.dim() == 3 and x.shape[-1] == INPUT_DIM:
            x = x.transpose(1, 2)  # (B, input_dim, seq_len)

        x = self.conv(x)
        x = x.transpose(1, 2)  # (B, seq_len, 32)
        out, _ = self.lstm(x)
        conv_out = self.head(out[:, -1, :])

        # GNN-like feature mixing and direct linear residual pathway.
        graph_out = self.gnn(x_flat)
        linear_out = self.lnn(x_flat)

        # Lightweight ViT-style branch: split the feature vector into patches,
        # project them to tokens, apply self-attention, and aggregate them.
        patch_size = self.vit_patch_size
        if x_flat.dim() == 2:
            batch_size, feature_dim = x_flat.shape
            pad = (patch_size - (feature_dim % patch_size)) % patch_size
            if pad:
                x_flat = F.pad(x_flat, (0, pad))
            patches = x_flat.reshape(batch_size, -1, patch_size)
            tokens = self.vit_patch_proj(patches)
            max_tokens = self.vit_pos_embed.shape[1]
            if tokens.shape[1] > max_tokens:
                tokens = tokens[:, :max_tokens, :]
            tokens = tokens + self.vit_pos_embed[:, :tokens.shape[1], :]
            attn_out, _ = self.vit_attn(tokens, tokens, tokens)
            vit_feat = self.vit_norm(attn_out.mean(dim=1))
            vit_out = self.vit_head(vit_feat)
        else:
            vit_out = self.vit_head(torch.zeros(x_flat.shape[0], self.vit_embed_dim, device=x_flat.device))

        return conv_out + graph_out + linear_out + vit_out


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