# Ground-truth pass of the property chapter stubs (first level)

Run on 2026-11-22. For each stub: the citekeys it uses, and whether `references.bib` gives each a local PDF in `references/`. A claim whose citekey has a local PDF is *checkable*; this pass checked the claims listed under "Checked by reading the page", and the rest of the sourced claims are checkable and not yet checked (the full pass is run when the chapter is developed, step 7). Claims that the stubs mark as from memory or without a source are listed under "Open" in each stub, and are not repeated here.

## meaning_as_difference

18 citekeys; 17 with a local PDF; without a local PDF: saussure1916cours; not in references.bib: none.

## meaning_as_direction

7 citekeys; 7 with a local PDF; without a local PDF: none; not in references.bib: none.

## meaning_as_region

17 citekeys; 17 with a local PDF; without a local PDF: none; not in references.bib: none.

## meaning_as_path

5 citekeys; 5 with a local PDF; without a local PDF: none; not in references.bib: none.

## meaning_as_composition

13 citekeys; 12 with a local PDF; without a local PDF: montague1970universal; not in references.bib: none.

## meaning_across_scales

10 citekeys; 10 with a local PDF; without a local PDF: none; not in references.bib: none.

## meaning_across_senses

21 citekeys; 21 with a local PDF; without a local PDF: none; not in references.bib: none.

## meaning_as_arrangement

7 citekeys; 6 with a local PDF; without a local PDF: saussure1916cours; not in references.bib: none.

## meaning_in_context

50 citekeys; 50 with a local PDF; without a local PDF: none; not in references.bib: none.

## meaning_and_truth

20 citekeys; 17 with a local PDF; without a local PDF: nagarjuna1995fundamental, priest2002beyond, tarski1944semantic; not in references.bib: none.

## meaning_as_generation

7 citekeys; 4 with a local PDF; without a local PDF: chomsky1957syntactic, chomsky1965aspects, chomsky1986knowledge; not in references.bib: none.

## Checked by reading the page

- Winoground (Thrush et al. 2022, PDF 6): human 89.50, 88.50 and 85.50 on the text, image and group scores; the best model scores are 38.00 (UNITER large, text), 20.50 (FLAVA, image) and 14.50 (VinVL, group), chance 25, 25 and 16.67. The stubs say "the best model of the original study 38" for the text score: correct as the best text score.
- Wei et al. (2018): human accuracy 80 per cent and T-CAM 76 and 72 per cent (Table 9, PDF 8); removing black frames lowers accuracy from 98 to 90 per cent and removing camera motion from 88 to 75 per cent on UCF101 (Table 1, PDF 4). The earlier text said "about 80 per cent on real videos, close to people" and "about 10 points each"; corrected in `meaning_as_path` to 72 to 76 against 80, and about 8 and 13 points.
- Arora, Liang and Ma (2017, PDF 1 and 2): a weighted average of word vectors with the first principal component removed beats the unweighted average by 10 to 30 per cent on textual similarity and beats some supervised RNN and LSTM methods; the stub says "rivals trained sentence encoders", which is milder and holds.
- Lake and Baroni (2018, PDF 1): the abstract states the compositional-skills question; the stub says networks "generalize to new combinations of known parts only partly", from memory of the results, and is marked to be read.
- SimLex-999 carries a concreteness rating for each word (`conc(w1)`, `conc(w2)` in the pinned archive): the experiment of the senses chapter can be built on it.

## Not verified in this pass

The claims copied from the earlier technology chapters (the salvaged sections) keep the readings that those chapters recorded and were not rechecked; the claims marked in the stubs as from memory or without a source (Saussure at the page, Frege on the context principle, Belnap, Reiter, Boden, Swanson, Mikolov 2013 on aligning languages, Gärdenfors on events, logic tensor networks, the benchmark comparisons for retrieval and for knowledge-graph models) have no PDF in the collection.