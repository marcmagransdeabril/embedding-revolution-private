"""Chomsky's Staircase, question 3: a Brainf*** interpreter, the Turing-complete rung in about 20 lines."""
from collections import defaultdict


def run(program: str, max_steps: int = 100_000):
    """Run a Brainf*** program (six instructions, no input) for at most `max_steps` instructions.

    Returns (printed_values, cells_used, halted). The tape is unbounded to the right: it is not limited by the
    length of the program. If the step budget runs out, `halted` is False, and that is all we can say.
    """
    jump, stack = {}, []
    for i, op in enumerate(program):  # match the brackets once, with a stack
        if op == "[":
            stack.append(i)
        elif op == "]":
            j = stack.pop()
            jump[i], jump[j] = j, i

    tape, ptr, pc, out, steps = defaultdict(int), 0, 0, [], 0
    while pc < len(program) and steps < max_steps:
        steps += 1
        op = program[pc]
        if op == ">":
            ptr += 1
        elif op == "<":
            ptr -= 1
        elif op == "+":
            tape[ptr] += 1
        elif op == "-":
            tape[ptr] -= 1
        elif op == ".":
            out.append(tape[ptr])
        elif op == "[" and tape[ptr] == 0:
            pc = jump[pc]
        elif op == "]" and tape[ptr] != 0:
            pc = jump[pc]
        pc += 1
    return out, len(tape), pc >= len(program)


def main():
    # 8 * 8 + 1 = 65: a loop, a second cell and arithmetic.
    out, cells, halted = run("++++++++[>++++++++<-]>+.")
    assert (out, halted) == ([65], True)

    # A 5-instruction program that needs one more cell for every extra step it is allowed to run:
    # no tape whose length is proportional to the program (or to any input) is enough.
    program = "+[>+]"
    used = {budget: run(program, budget) for budget in (1_000, 10_000)}
    assert not used[1_000][2] and not used[10_000][2]  # still running when the budget ends
    assert used[1_000][1] > 10 * len(program) and used[10_000][1] > 5 * used[1_000][1]

    # An endless loop in two instructions: the interpreter cannot tell it from a very slow program.
    assert not run("+[]", 50_000)[2]
    print(f"{out} | {program!r} after 10,000 steps: {used[10_000][1]} cells and still running")


if __name__ == "__main__":
    main()
