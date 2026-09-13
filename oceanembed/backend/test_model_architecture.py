import numpy as np

from model import OceanNetCNNLSTM


def test_cnn_lstm_accepts_feature_vector():
    model = OceanNetCNNLSTM()
    x = np.random.randn(4, 5).astype(np.float32)
    y = model.__call__(x)
    assert y.shape == (4, 2)
    assert hasattr(model, "gnn")
    assert hasattr(model, "lnn")
    assert hasattr(model, "vit")
    assert hasattr(model, "conv")
    assert hasattr(model, "lstm")
