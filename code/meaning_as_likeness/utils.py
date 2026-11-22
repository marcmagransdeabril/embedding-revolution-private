"""Shared helpers for the scripts of the chapter "Likeness as Nearness": pinned downloads, the training text (text8), the judges
(SimLex-999 with its association column, WordSim-353 with its raters, the Google analogies), the co-occurrence counts, and the
statistics that every experiment reports (Spearman correlation, bootstrap over pairs, overlap of nearest neighbours).

Nothing is committed that can be downloaded: every external file is named by its URL and pinned by a SHA-256 that `fetch` checks, and
a mismatch stops the script. The files are kept in `.cache/` next to this file (ignored by git).
"""
from __future__ import annotations

import hashlib
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.stats import spearmanr

CACHE = Path(__file__).parent / ".cache"

# --- pinned downloads: url -> sha256 of the file as downloaded on 2026-11-22
TEXT8_URL = "http://mattmahoney.net/dc/text8.zip"
TEXT8_SHA256 = "a6640522afe85d1963ad56c05b0ede0a0c000dddc9671758a6cc09b7a38e5232"
SIMLEX_URL = "https://fh295.github.io/SimLex-999.zip"
SIMLEX_SHA256 = "30f40eb18f41b08b65dfbc328f473e8b69ba444b1c9d053c1adde2324fc76315"
WS353_URL = "https://gabrilovich.com/resources/data/wordsim353/wordsim353.zip"
WS353_SHA256 = "4f12a5fe9650184662306f8ae72c7e6bb44c2627e0275e9f9c6eb067e3441a22"
ANALOGY_URL = "https://raw.githubusercontent.com/tmikolov/word2vec/master/questions-words.txt"
ANALOGY_SHA256 = "8c29b3332afc46f3fb8be04cb5297bf96f39aa7131272dff57869b4485b22a36"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch(url: str, sha256: str) -> Path:
    """Path of the file at `url` in the cache, downloaded if absent. The SHA-256 is checked every time."""
    CACHE.mkdir(exist_ok=True)
    dest = CACHE / url.rsplit("/", 1)[1]
    if not dest.exists():
        urllib.request.urlretrieve(url, dest)
    if sha256_of(dest) != sha256:
        raise ValueError(f"{dest} does not match the pinned SHA-256 of {url}")
    return dest


# --- the training text
def load_text8() -> list[str]:
    """The 17,005,207 lowercased words of text8 (the first 100 MB of English Wikipedia, cleaned)."""
    with zipfile.ZipFile(fetch(TEXT8_URL, TEXT8_SHA256)) as z:
        return z.read("text8").decode("ascii").split()


def build_vocab(words: list[str], size: int) -> tuple[list[str], np.ndarray]:
    """The `size` most frequent words, and the text as an array of their indices (-1 for the words left out)."""
    counts = Counter(words)
    vocab = [w for w, _ in counts.most_common(size)]
    index = {w: i for i, w in enumerate(vocab)}
    return vocab, np.fromiter((index.get(w, -1) for w in words), dtype=np.int32, count=len(words))


def cooccurrence(ids: np.ndarray, size: int, window: int) -> sparse.csr_matrix:
    """Symmetric matrix of how many times two words stand within `window` positions of each other (out-of-vocabulary words are
    skipped but still occupy a position)."""
    total = sparse.csr_matrix((size, size), dtype=np.float32)
    for offset in range(1, window + 1):
        a, b = ids[:-offset], ids[offset:]
        keep = (a >= 0) & (b >= 0)
        pairs = sparse.coo_matrix((np.ones(keep.sum(), dtype=np.float32), (a[keep], b[keep])), shape=(size, size)).tocsr()
        total = total + pairs
    return (total + total.T).tocsr()


def ppmi(counts: sparse.csr_matrix) -> sparse.csr_matrix:
    """Positive pointwise mutual information in bits of a sparse symmetric count matrix (zero where the pair never occurs)."""
    c = counts.tocoo()
    total = c.data.sum()
    p_w = np.asarray(counts.sum(axis=1)).ravel() / total
    pmi = np.log2(c.data / total / (p_w[c.row] * p_w[c.col]))
    keep = pmi > 0
    return sparse.coo_matrix((pmi[keep].astype(np.float32), (c.row[keep], c.col[keep])), shape=counts.shape).tocsr()


# --- the judges
def load_simlex() -> list[tuple[str, str, float, float]]:
    """(word1, word2, similarity, association) for the 999 pairs of SimLex-999; association is the USF free-association strength."""
    with zipfile.ZipFile(fetch(SIMLEX_URL, SIMLEX_SHA256)) as z:
        lines = z.read("SimLex-999/SimLex-999.txt").decode("utf-8").splitlines()
    rows = [l.split("\t") for l in lines[1:]]
    return [(r[0], r[1], float(r[3]), float(r[7])) for r in rows]


def load_ws353() -> tuple[list[tuple[str, str, float]], np.ndarray]:
    """(word1, word2, mean rating) for the 353 pairs of WordSim-353, and the matrix of the individual ratings (pairs x raters, NaN
    where a rater did not rate). The 13 raters of set 1 and the 16 of set 2 are different people, so the matrix has 29 columns."""
    with zipfile.ZipFile(fetch(WS353_URL, WS353_SHA256)) as z:
        combined = z.read("combined.tab").decode("utf-8", "replace").splitlines()[1:]
        sets = [z.read(f"set{i}.tab").decode("utf-8", "replace").splitlines()[1:] for i in (1, 2)]
    pairs = [(r[0].lower(), r[1].lower(), float(r[2])) for r in (l.split("\t") for l in combined if l.strip())]
    ratings = np.full((len(pairs), 29), np.nan)
    where = {(a, b): i for i, (a, b, _) in enumerate(pairs)}
    for k, lines in enumerate(sets):
        base = 13 * k
        for l in lines:
            r = [x.strip() for x in l.split("\t")]
            if len(r) < 4 or not r[0]:
                continue
            vals = [float(x) for x in r[3:] if x]
            ratings[where[(r[0].lower(), r[1].lower())], base: base + len(vals)] = vals
    return pairs, ratings


def load_analogies() -> dict[str, list[tuple[str, str, str, str]]]:
    """The 19,544 questions a : b :: c : d of the Google analogy set, by category."""
    out: dict[str, list] = {}
    cat = ""
    for line in fetch(ANALOGY_URL, ANALOGY_SHA256).read_text().splitlines():
        if line.startswith(":"):
            cat = line[2:]
            out[cat] = []
        elif line.strip():
            out[cat].append(tuple(line.lower().split()))
    return out


def ceiling(ratings: np.ndarray) -> tuple[float, float]:
    """Agreement between raters: (mean correlation of one rater with the mean of the others, mean pairwise correlation).
    Pairs and raters with missing ratings are dropped rater by rater."""
    n_raters = ratings.shape[1]
    one_vs_rest, pairwise = [], []
    for r in range(n_raters):
        rated = ~np.isnan(ratings[:, r])
        if rated.sum() < 10:
            continue
        others = np.nanmean(np.delete(ratings, r, axis=1)[rated], axis=1)
        ok = ~np.isnan(others)
        one_vs_rest.append(spearmanr(ratings[rated, r][ok], others[ok]).statistic)
        for s in range(r + 1, n_raters):
            both = rated & ~np.isnan(ratings[:, s])
            if both.sum() >= 10:
                pairwise.append(spearmanr(ratings[both, r], ratings[both, s]).statistic)
    return float(np.mean(one_vs_rest)), float(np.mean(pairwise))


# --- statistics
def unit(x: np.ndarray) -> np.ndarray:
    """Rows scaled to length 1 (a zero row stays zero)."""
    n = np.linalg.norm(x, axis=1, keepdims=True)
    return np.divide(x, n, out=np.zeros_like(x), where=n > 0)


def pair_scores(emb: np.ndarray, index: dict[str, int], pairs: list[tuple], kind: str = "cosine") -> tuple[np.ndarray, np.ndarray]:
    """The score of each judged pair whose two words are both in the vocabulary, and the positions of those pairs in `pairs`."""
    keep = np.array([i for i, p in enumerate(pairs) if p[0] in index and p[1] in index], dtype=int)
    a = emb[[index[pairs[i][0]] for i in keep]]
    b = emb[[index[pairs[i][1]] for i in keep]]
    if kind == "cosine":
        a, b = unit(a), unit(b)
    return (a * b).sum(axis=1), keep


def spearman_interval(score: np.ndarray, judge: np.ndarray, resamples: int = 1000, seed: int = 0) -> tuple[float, float, float]:
    """Spearman correlation of a score with a judge, and its percentile-bootstrap 95% interval over pairs."""
    rho = float(spearmanr(score, judge).statistic)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(resamples):
        pick = rng.integers(0, len(score), len(score))
        boots.append(spearmanr(score[pick], judge[pick]).statistic)
    low, high = np.nanpercentile(boots, [2.5, 97.5])
    return rho, float(low), float(high)


def nearest(emb: np.ndarray, queries: np.ndarray, k: int, chunk: int = 2000) -> np.ndarray:
    """The k nearest neighbours by cosine (the word itself excluded) of each query word, as an array (queries x k)."""
    u = unit(emb)
    out = np.empty((len(queries), k), dtype=np.int32)
    for s in range(0, len(queries), chunk):
        q = queries[s: s + chunk]
        sims = u[q] @ u.T
        sims[np.arange(len(q)), q] = -np.inf
        top = np.argpartition(-sims, k, axis=1)[:, :k]
        order = np.argsort(-np.take_along_axis(sims, top, axis=1), axis=1)
        out[s: s + chunk] = np.take_along_axis(top, order, axis=1)
    return out


def neighbour_overlap(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """For each row, the fraction of the neighbours of `a` that are also neighbours of `b`."""
    return np.array([len(set(x) & set(y)) / len(x) for x, y in zip(a, b)])


# --- the trained spaces (made by train_spaces.py)
SPACES = CACHE / "spaces"
RESULTS = Path(__file__).parent / "results"
FIGURES = Path(__file__).resolve().parents[2] / "figures" / "likeness_as_nearness"


def cached(stem: str, extension: str) -> Path:
    """Path of a file made by train_spaces.py (the name is built here so that it is not taken for a committed data file)."""
    return SPACES / f"{stem}.{extension}"


def load_space(name: str) -> np.ndarray:
    path = SPACES / f"{name}.npy"
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing: run train_spaces.py first")
    return np.load(path)


def load_vocab() -> tuple[list[str], dict[str, int], np.ndarray]:
    """The 30,000-word vocabulary of the trained spaces, its index and the counts of its words in the training text."""
    import json
    vocab = json.loads(cached("vocab", "json").read_text())
    return vocab, {w: i for i, w in enumerate(vocab)}, np.load(cached("counts", "npy"))


def save_results(name: str, results: dict) -> None:
    """Keep the numbers of an experiment in code/likeness_as_nearness/results/<name>.json, for the text of the chapter."""
    import json
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"{name}.json").write_text(json.dumps(results, indent=1, sort_keys=True))
