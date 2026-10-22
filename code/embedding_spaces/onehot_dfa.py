"""The Discrete Collapse, question 1: a finite automaton is a product of 0/1 matrices on a one-hot state."""
import itertools

import numpy as np

# Automaton that accepts the binary strings with an even number of 1s. State 0 = even, state 1 = odd.
T = {
    "0": np.array([[1, 0], [0, 1]]),  # reading a 0 keeps the state
    "1": np.array([[0, 1], [1, 0]]),  # reading a 1 swaps the two states
}
for m in T.values():  # every column has exactly one 1: the move of one state is deterministic
    assert (m.sum(axis=0) == 1).all() and ((m == 0) | (m == 1)).all()


def accepts(s: str) -> bool:
    state = np.array([1, 0])  # one-hot vector of the initial state "even"
    for ch in s:
        state = T[ch] @ state  # reading a symbol = multiplying by its matrix
    return bool(state[0])  # accept if the final state is "even"


for n in range(11):
    for bits in itertools.product("01", repeat=n):
        s = "".join(bits)
        assert accepts(s) == (s.count("1") % 2 == 0), s
print("matrices agree with the parity of 1s on every binary string of up to 10 symbols")

# Probabilistic version: a reading of a 1 that works with probability 0.9 and is ignored otherwise.
noisy = 0.9 * T["1"] + 0.1 * T["0"]
assert np.allclose(noisy.sum(axis=0), 1)  # columns now are probability distributions
state = np.array([1.0, 0.0])
for _ in range(3):
    state = noisy @ state
print("after reading 111 with a noisy automaton: P(even), P(odd) =", state.round(3))
