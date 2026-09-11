import numpy as np
from model import OceanEmbedPredictor, build_feature_vector_simple

predictor = OceanEmbedPredictor().load()

# Test: surface_temp, surface_sal, depth, lat_norm, lon_norm
# Pick a realistic Indian Ocean surface reading at moderate depth
test_input = np.array([
    [28.5, 35.0, 100.0, 0.15, 0.40],   # warm surface, 100m depth
    [28.5, 35.0, 500.0, 0.15, 0.40],   # same location, 500m depth (should be colder)
    [22.0, 34.5, 50.0, 0.60, 0.20],    # different region
])

preds = predictor.predict(test_input)
for i, (inp, pred) in enumerate(zip(test_input, preds)):
    print(f"Input {i}: {inp} -> Predicted temp={pred[0]:.2f}°C, salinity={pred[1]:.3f} psu")