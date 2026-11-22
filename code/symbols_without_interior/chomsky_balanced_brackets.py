"""Chomsky's Staircase, question 1: balanced brackets need a stack (a pushdown automaton)."""

PAIRS = {")": "(", "]": "[", "}": "{"}


def balanced(s: str) -> bool:
    """Push every opening bracket; on a closing one, pop and check that it is the partner."""
    stack = []
    for ch in s:
        if ch in PAIRS.values():
            stack.append(ch)
        elif ch in PAIRS:
            if not stack or stack.pop() != PAIRS[ch]:
                return False
    return not stack  # accept only if every bracket was closed


def main():
    for s in ("", "()", "(()[]{()})", "{[()()]}"):
        assert balanced(s), s
    for s in ("(", "(()", "())(", "([)]", "{[}]"):
        assert not balanced(s), s
    print("balanced: all examples as expected")


if __name__ == "__main__":
    main()
