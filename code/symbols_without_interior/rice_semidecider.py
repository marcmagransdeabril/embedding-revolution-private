"""Rice's Theorem, question 2: a step-limited test answers "yes", "no" or "unknown", and "unknown" never goes away for loops."""


# A program is a generator: it does one step of work at each `yield` and returns its result when it ends.
def quick():
    yield
    return 65


def other():
    yield
    return 1


def slow():  # halts, but only after 5,000 steps
    for _ in range(5_000):
        yield
    return 65


def forever():
    while True:
        yield


def check(program, budget: int):
    """True if the program finishes within `budget` steps with result 65, False if it finishes with another result,
    None ("unknown") if the budget runs out first."""
    steps = program()
    for _ in range(budget):
        try:
            next(steps)
        except StopIteration as done:
            return done.value == 65
    return None


def main():
    assert check(quick, 10) is True and check(quick, 10_000) is True
    assert check(other, 10) is False  # halts with another result: a definite "no"
    assert check(slow, 10) is None  # unknown with a small budget...
    assert check(slow, 5_000) is None and check(slow, 5_001) is True  # ...and "yes" once the budget is large enough
    assert all(check(forever, b) is None for b in (10, 10_000, 1_000_000))  # unknown at every budget
    print("check: True/False when the program halts within the budget, None for every program that does not")


if __name__ == "__main__":
    main()
