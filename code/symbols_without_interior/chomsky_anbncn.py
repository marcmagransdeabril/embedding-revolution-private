"""Chomsky's Staircase, question 2: {a^n b^n c^n} needs a linear-bounded automaton, not a pushdown one."""
import itertools
import re


def in_language_lba(s: str) -> bool:
    """Linear-bounded automaton: works only inside the input, overwriting cells with marks.

    Extra memory is a constant number of variables (the head position and a state), no matter how long
    `s` is. Each pass crosses off one `a`, one `b` and one `c`.
    """
    if not re.fullmatch(r"a*b*c*", s):  # a finite automaton can check the shape
        return False
    tape = list(s)
    while True:
        crossed = 0  # how many of a, b, c we crossed off in this pass
        for symbol in "abc":
            head = 0
            while head < len(tape) and tape[head] != symbol:  # scan right for the first uncrossed symbol
                head += 1
            if head < len(tape):
                tape[head] = symbol.upper()  # cross it off
                crossed += 1
        if crossed == 0:
            return True  # nothing left: all three letters ran out together
        if crossed < 3:
            return False  # one letter ran out before the others


def in_language_pushdown_attempt(s: str) -> bool:
    """Best a stack can do: match the b's against the a's. The count is gone when the c's arrive."""
    stack = []
    i = 0
    while i < len(s) and s[i] == "a":
        stack.append("a")
        i += 1
    while i < len(s) and s[i] == "b":
        if not stack:
            return False
        stack.pop()
        i += 1
    if stack:
        return False
    return all(ch == "c" for ch in s[i:])  # nothing left to compare the c's against


def main():
    def reference(s):
        n = len(s) // 3
        return s == "a" * n + "b" * n + "c" * n

    for length in range(10):
        for chars in itertools.product("abc", repeat=length):
            s = "".join(chars)
            assert in_language_lba(s) == reference(s), s

    assert in_language_lba("") and in_language_lba("abc") and in_language_lba("a" * 50 + "b" * 50 + "c" * 50)
    assert not in_language_lba("aabbc") and not in_language_lba("aabbccc") and not in_language_lba("abcabc")

    # The stack version accepts a^n b^n c^m for every m, including wrong ones.
    assert in_language_pushdown_attempt("aabbcc")
    assert in_language_pushdown_attempt("aabbccccc")  # wrongly accepted: five c's, only two a's
    print("in_language_lba agrees with the definition on all strings up to length 9")


if __name__ == "__main__":
    main()
