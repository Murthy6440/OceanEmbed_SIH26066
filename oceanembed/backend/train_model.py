"""
Train OceanEmbed on REAL Argo float data and compute validation metrics
(RMSE, correlation, bias) on a held-out real test split.
"""
import json
import os

import numpy as np
import torch
import torch.nn as nn

from model import OceanNet, Scaler, MODEL_DIR, MODEL_PATH, X_SCALER_PATH, Y_SCALER_PATH, METRICS_PATH

SEED = 42
EPOCHS = 20
BATCH_SIZE = 2048
LR = 1e-3


def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


def mae(a, b):
    return float(np.mean(np.abs(a - b)))


def bias(pred, true):
    return float(np.mean(pred - true))


def pearson_corr(a, b):
    if np.std(a) == 0 or np.std(b) == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def r2_score(pred, true):
    if np.var(true) == 0:
        return 0.0
    ss_res = np.sum((true - pred) ** 2)
    ss_tot = np.sum((true - np.mean(true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return float(1.0 - ss_res / ss_tot)


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)
    torch.manual_seed(SEED)

    print("Loading REAL Argo data...")
    X = np.load("argo_X_full_india_clean.npy").astype(np.float32)
    y = np.load("argo_y_full_india_clean.npy").astype(np.float32)

    n_total = len(X)
    rng = np.random.default_rng(SEED)
    idx = rng.permutation(n_total)
    n_test = int(n_total * 0.1)
    test_idx, train_idx = idx[:n_test], idx[n_test:]

    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    x_scaler = Scaler().fit(X_train)
    y_scaler = Scaler().fit(y_train)

    Xtr = torch.from_numpy(x_scaler.transform(X_train))
    ytr = torch.from_numpy(y_scaler.transform(y_train))
    Xte = torch.from_numpy(x_scaler.transform(X_test))

    model = OceanNet()
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loss_fn = nn.MSELoss()

    n = Xtr.shape[0]
    print("Training on real data...")
    for epoch in range(EPOCHS):
        perm = torch.randperm(n)
        total_loss = 0.0
        for i in range(0, n, BATCH_SIZE):
            b = perm[i:i + BATCH_SIZE]
            xb, yb = Xtr[b], ytr[b]
            opt.zero_grad()
            pred = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            opt.step()
            total_loss += loss.item() * len(b)
        print(f"  epoch {epoch+1:3d}/{EPOCHS}  train_mse={total_loss/n:.5f}")

    model.eval()
    with torch.no_grad():
        pred_test_scaled = model(Xte).numpy()
    pred_test = y_scaler.inverse_transform(pred_test_scaled)

    temp_pred, sal_pred = pred_test[:, 0], pred_test[:, 1]
    temp_true, sal_true = y_test[:, 0], y_test[:, 1]

    metrics = {
        "note": "Computed on REAL Argo float data (Indian Ocean region).",
        "n_test_samples": len(y_test),
        "temperature": {
            "mae": mae(temp_pred, temp_true),
            "rmse": rmse(temp_pred, temp_true),
            "r2": r2_score(temp_pred, temp_true),
            "correlation": pearson_corr(temp_pred, temp_true),
            "bias": bias(temp_pred, temp_true),
            "units": "deg C",
        },
        "salinity": {
            "mae": mae(sal_pred, sal_true),
            "rmse": rmse(sal_pred, sal_true),
            "r2": r2_score(sal_pred, sal_true),
            "correlation": pearson_corr(sal_pred, sal_true),
            "bias": bias(sal_pred, sal_true),
            "units": "psu",
        },
    }

    torch.save(model.state_dict(), MODEL_PATH)
    x_scaler.save(X_SCALER_PATH)
    y_scaler.save(Y_SCALER_PATH)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print("\nSaved model to", MODEL_PATH)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()