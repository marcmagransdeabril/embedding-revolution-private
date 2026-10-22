"""The Orthogonal Catastrophe, question 2: a linear model on one-hot inputs transfers nothing between words."""
import numpy as np

from utils import DENSE, WORDS

ONE_HOT = np.eye(len(WORDS))
y = {"dawn": 1.0, "king": 0.0, "queen": 0.0}  # training labels: 1 = "is a time of day"


def sigmoid(t):
    return 1 / (1 + np.exp(-t))


def loss(w, xi, label):
    """Binary cross-entropy of one example."""
    p = sigmoid(w @ xi)
    return -(label * np.log(p) + (1 - label) * np.log(1 - p))


# The gradient of the loss with respect to w is (p - label) * x: check it against finite differences.
rng = np.random.default_rng(0)
w0, x0 = rng.normal(size=5), DENSE[WORDS.index("king")]
grad = (sigmoid(w0 @ x0) - 1.0) * x0
numeric = np.array([(loss(w0 + 1e-6 * np.eye(5)[k], x0, 1.0) - loss(w0 - 1e-6 * np.eye(5)[k], x0, 1.0)) / 2e-6
                    for k in range(5)])
assert np.allclose(grad, numeric, atol=1e-6)


def train(x: np.ndarray, steps=500, lr=0.5) -> np.ndarray:
    """Logistic regression p = sigmoid(w . x) without bias, trained by gradient descent on the three words."""
    w = np.zeros(x.shape[1])
    for _ in range(steps):
        for word, label in y.items():
            xi = x[WORDS.index(word)]
            w -= lr * (sigmoid(w @ xi) - label) * xi  # w <- w - lr * (p - y) * x
    return w


for name, x in (("one-hot", ONE_HOT), ("dense", DENSE)):
    w = train(x)
    p = sigmoid(x @ w)
    print(f"{name:8s}", {word: round(float(p[i]), 3) for i, word in enumerate(WORDS)})
    if name == "one-hot":
        assert p[WORDS.index("dusk")] == 0.5  # never trained, so the model knows nothing: probability 1/2
        assert p[WORDS.index("xqzv")] == 0.5
    else:
        assert p[WORDS.index("dusk")] > 0.9  # dusk was never seen, but it shares features with dawn
