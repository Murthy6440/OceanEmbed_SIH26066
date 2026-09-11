import numpy as np

X = np.load('argo_X_full_india.npy')
y = np.load('argo_y_full_india.npy')

valid = (
    (y[:, 1] >= 2) & (y[:, 1] <= 42) &
    (X[:, 1] >= 2) & (X[:, 1] <= 42)
)

print(f"Dropping {(~valid).sum()} bad rows out of {len(y)}")
X_clean, y_clean = X[valid], y[valid]

np.save('argo_X_full_india_clean.npy', X_clean)
np.save('argo_y_full_india_clean.npy', y_clean)
print("Clean shapes:", X_clean.shape, y_clean.shape)