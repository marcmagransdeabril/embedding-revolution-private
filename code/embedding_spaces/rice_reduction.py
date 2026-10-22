"""Rice's Theorem, question 2: the program M' of the proof, built from M, x and Q. A decider for P would decide halting."""


# A program is a generator function: it yields once per step of computation and returns its result.
def run(program, y, budget: int):
    """Result of `program(y)` if it finishes within `budget` steps, else None (unknown)."""
    steps = program(y)
    for _ in range(budget):
        try:
            next(steps)
        except StopIteration as done:
            return done.value
    return None


def Q(y):  # has P = "returns 1 on input 0"
    return 1
    yield  # unreachable, but makes Q a generator function


def halts_quickly(x):  # M that halts: 100 steps, then returns
    for _ in range(100):
        yield
    return "done"


def loops_forever(x):  # M that never halts
    while True:
        yield


def build(M, x):
    """M' of the proof: on input y, first run M on x and, if that halts, run Q on y."""
    def M_prime(y):
        yield from M(x)
        return (yield from Q(y))
    return M_prime


def has_P(program, budget: int):
    """Test of P = "returns 1 on input 0": True if it does, False if it halts with another value, None if unknown."""
    result = run(program, 0, budget)
    return None if result is None else result == 1


def main():
    # M halts, so M' behaves like Q and has P (for every budget large enough to finish).
    assert has_P(build(halts_quickly, x=0), budget=1_000) is True
    # M never halts, so M' never returns: it does not have P, but no budget can show it.
    assert all(has_P(build(loops_forever, x=0), budget=b) is None for b in (10, 1_000, 100_000))

    print("build(M, x) has P exactly when M halts on x")


if __name__ == "__main__":
    main()
