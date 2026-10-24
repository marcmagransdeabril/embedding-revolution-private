"""Rice's Theorem, question 2: questions next to Rice's theorem that ARE decidable (text, bounded running time, finite automata)."""
from collections import deque

from chomsky_bf_interpreter import run


def has_loop(program: str) -> bool:
    """(a) A property of the text: read it. Decidable, and not semantic."""
    return "[" in program


def prints_65_within(program: str, steps: int = 1_000) -> bool:
    """(b) "Halts within `steps` steps and prints exactly 65". The clock bounds the search, so running is a decider."""
    out, _, halted = run(program, steps)
    return halted and out == [65]


# (c) "halts and prints exactly 65" has no decider (Rice): the best we can do is the step-limited test of question 1.


def dfa_equivalent(a, b, alphabet="01") -> bool:
    """(d) Two DFAs, each (start, accepting_states, delta) with delta[(state, symbol)] = next state, accept the same
    strings iff no reachable pair of states (one from each) disagrees on acceptance. Finitely many pairs: it terminates."""
    (sa, fa, da), (sb, fb, db) = a, b
    seen, queue = {(sa, sb)}, deque([(sa, sb)])
    while queue:
        p, q = queue.popleft()
        if (p in fa) != (q in fb):
            return False
        for c in alphabet:
            nxt = (da[(p, c)], db[(q, c)])
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return True


def main():
    loop_program = "++++++++[>++++++++<-]>+."
    flat_program = "+" * 65 + "."
    assert has_loop(loop_program) and not has_loop(flat_program)  # same meaning, different text: the text question differs
    assert prints_65_within(loop_program) and prints_65_within(flat_program)
    assert not prints_65_within("+.") and not prints_65_within("+[]")  # "no" for +[] only means "not within 1,000 steps"

    # "even number of 1s" with 2 states, and the same language with 4 states (parity tracked twice)
    even2 = (0, {0}, {(s, c): (s ^ (c == "1")) for s in (0, 1) for c in "01"})
    even4 = ((0, 0), {(0, 0), (0, 1)}, {((x, y), c): (x ^ (c == "1"), y ^ (c == "1")) for x in (0, 1) for y in (0, 1) for c in "01"})
    # "even length": toggles on every symbol
    even_length = (0, {0}, {(s, c): 1 - s for s in (0, 1) for c in "01"})
    assert dfa_equivalent(even2, even4)  # different machines, same language: decided
    assert not dfa_equivalent(even2, even_length)  # the string "0" tells them apart
    print("text, bounded-time and finite-automaton questions are decidable; 'halts and prints 65' is only semi-decidable")


if __name__ == "__main__":
    main()
