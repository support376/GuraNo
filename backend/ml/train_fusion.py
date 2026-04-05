"""
Train the fusion model (Logistic Regression on 3 modality scores).
Usage: python -m ml.train_fusion
"""
import pickle
import os
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

# Synthetic training data for MVP
# Format: [voice_score, face_score, hr_score] -> label (0=truth, 1=lie)
np.random.seed(42)

N = 500

# Generate truth samples (low scores)
truth_voice = np.random.beta(2, 5, N // 2)
truth_face = np.random.beta(2, 5, N // 2)
truth_hr = np.random.beta(2, 5, N // 2)
truth_X = np.column_stack([truth_voice, truth_face, truth_hr])
truth_y = np.zeros(N // 2)

# Generate lie samples (higher scores)
lie_voice = np.random.beta(4, 3, N // 2)
lie_face = np.random.beta(3, 3, N // 2)
lie_hr = np.random.beta(5, 3, N // 2)
lie_X = np.column_stack([lie_voice, lie_face, lie_hr])
lie_y = np.ones(N // 2)

X = np.vstack([truth_X, lie_X])
y = np.concatenate([truth_y, lie_y])

# Shuffle
idx = np.random.permutation(len(X))
X, y = X[idx], y[idx]

# Train
model = LogisticRegression(C=1.0, max_iter=1000)
model.fit(X, y)

# Evaluate
scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
print(f"Cross-validation accuracy: {scores.mean():.3f} +/- {scores.std():.3f}")
print(f"Coefficients: voice={model.coef_[0][0]:.3f}, face={model.coef_[0][1]:.3f}, hr={model.coef_[0][2]:.3f}")

# Save
save_dir = os.path.join(os.path.dirname(__file__), "saved_models")
os.makedirs(save_dir, exist_ok=True)
model_path = os.path.join(save_dir, "fusion_lr.pkl")
with open(model_path, "wb") as f:
    pickle.dump(model, f)

print(f"Model saved to {model_path}")
