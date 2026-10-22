"""Rice's Theorem, question 1: a step-limited test of a semantic property answers "yes" or "unknown", never a firm "no" for loops."""
from chomsky_bf_interpreter import run


def prints_65(program: str, budget: int):
    """Semantic property P = "halts and prints exactly 65". True/False if the program halts within `budget`
    steps, None ("unknown") if the budget runs out first."""
    out, _, halted = run(program, budget)
    if not halted:
        return None
    return out == [65]


def main():
    loop_program = "++++++++[>++++++++<-]>+."  # 8 * 8 + 1 = 65
    flat_program = "+" * 65 + "."  # same behaviour, different text
    assert loop_program != flat_program
    assert prints_65(loop_program, 1_000) is True and prints_65(flat_program, 1_000) is True

    assert prints_65("+.", 1_000) is False  # halts and prints 1: a definite "no"

    # Endless loops: "unknown" at every budget we try, however large.
    for forever in ("+[]", "+[>+]", loop_program[:-1] + ".[]"):  # the last one prints 65 and then never stops
        assert all(prints_65(forever, b) is None for b in (10, 1_000, 100_000)), forever

    # A slow program that does halt: "unknown" with a small budget, "yes" once the budget is large enough.
    slow = "+" * 30 + "[>" + "+" * 30 + "[>+<-]<-]>>[-]" + "+" * 65 + "."  # a few thousand steps, then prints 65
    assert prints_65(slow, 1_000) is None
    assert prints_65(slow, 1_000_000) is True
    print("prints_65: True/False when the program halts within the budget, None for every program that does not")


if __name__ == "__main__":
    main()
