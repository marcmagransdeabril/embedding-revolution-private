"""The Orthogonal Catastrophe, question 4: a real tokenizer is the dictionary behind the one-hot vectors."""
import numpy as np
from tokenizers import Tokenizer

PHRASE = "Attack at dawn, unbelievably... 🙂 xqzv!"


def main() -> None:
    tok = Tokenizer.from_pretrained("bert-base-uncased")  # downloaded once from the Hugging Face Hub, then cached
    enc = tok.encode(PHRASE)
    assert len(enc.tokens) == len(enc.ids)  # one id per token, in the same order
    pairs = [f"{token:>6} {i:>5}" for token, i in zip(enc.tokens, enc.ids)]
    for k in range(0, len(pairs), 4):  # four token-number pairs per row, in phrase order
        print("  ".join(pairs[k:k + 4]))

    # The id is the index of the hot entry: the one-hot vector of a token has a single 1 at that position.
    size = tok.get_vocab_size()
    o = np.zeros(size)
    o[enc.ids[3]] = 1  # "dawn"
    assert enc.tokens[3] == "dawn" and o.sum() == 1 and o.argmax() == enc.ids[3]
    print(f"vocabulary: {size} words, so each token is a vector of {size} entries with a single 1 (dawn: position {enc.ids[3]})")


if __name__ == "__main__":
    main()
