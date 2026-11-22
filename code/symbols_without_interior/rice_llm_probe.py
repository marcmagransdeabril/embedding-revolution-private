"""Rice's Theorem, question 1: ground truth for an LLM that explains programs. Variants of one program, and a program whose halting nobody knows."""


def steps(n):  # the seed program: how many Collatz steps until n reaches 1
    count = 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else 3 * n + 1
        count += 1
    return count


def steps_recursive(n):  # variation 1: recursion instead of a loop
    return 0 if n == 1 else 1 + steps_recursive(n // 2 if n % 2 == 0 else 3 * n + 1)


def steps_obfuscated(m):  # variation 2: other names, dead code, a different control structure
    unused, total = 42, 0
    while True:
        if m == 1:
            break
        if unused > 100:
            m = 0  # dead code: never runs
        m = m >> 1 if not m & 1 else m + m + m + 1
        total += 1
    return total


def reaches_one_minus(n, limit=10_000):
    """Variation 3: change one character, 3n+1 -> 3n-1. Returns ('halts', steps), or ('loops', None) once a value repeats.
    Here a repeated value is a proof of looping, because the program has no other state: this particular program can be decided."""
    seen, count = set(), 0
    while n != 1:
        if n in seen:
            return "loops", None
        seen.add(n)
        n = n // 2 if n % 2 == 0 else 3 * n - 1
        count += 1
        if count > limit:
            return "unknown", None
    return "halts", count


def is_prime(k):
    return k > 1 and all(k % d for d in range(2, int(k**0.5) + 1))


def goldbach_counterexample(limit):
    """Variation 4: the first even number above 2 that is not a sum of two primes, or None up to `limit`.
    The program `while True: ...` that stops at that number halts if and only if Goldbach's conjecture is false."""
    for even in range(4, limit, 2):
        if not any(is_prime(p) and is_prime(even - p) for p in range(2, even // 2 + 1)):
            return even
    return None


def main():
    assert steps(27) == steps_recursive(27) == steps_obfuscated(27) == 111  # three texts, one behaviour
    assert reaches_one_minus(27) == ("loops", None)  # one character, a different behaviour
    assert reaches_one_minus(1) == ("halts", 0)
    assert goldbach_counterexample(10_000) is None  # no counterexample so far, as for every one tried up to 4e18
    print("steps(27) = 111 in three versions; the 3n-1 version loops; no Goldbach counterexample below 10,000")


if __name__ == "__main__":
    main()
