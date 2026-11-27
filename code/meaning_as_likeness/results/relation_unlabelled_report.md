# Q3, test 1: an open rater on far pairs (claude-opus-5.5)

1600 known pairs (control) and 2000 far in both pairs, 200 near in both pairs, 2000 random, no relation pairs, 1000 random, any pairs, mixed blind. Intervals: 95% bootstrap over the pairs.

## Control

| relation | canonical name | recall | any relation | none |
|---|---|---|---|---|
| inflection | inflection | 91.5% [87.5, 95.0] | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] |
| derivation | derivation | 98.0% [96.0, 99.5] | 100.0% [100.0, 100.0] | 0.0% [0.0, 0.0] |
| synonym | synonym | 87.5% [83.0, 92.0] | 98.0% [96.0, 99.5] | 2.0% [0.5, 4.0] |
| antonym | antonym | 95.5% [92.0, 98.5] | 99.0% [97.5, 100.0] | 1.0% [0.0, 2.5] |
| hypernym | hypernym | 45.0% [38.5, 52.0] | 89.5% [85.0, 93.5] | 10.5% [6.5, 15.0] |
| meronym | meronym | 71.5% [65.0, 77.5] | 96.5% [93.5, 98.5] | 3.5% [1.5, 6.5] |
| co-hyponym | co-hyponym | 33.0% [27.0, 39.5] | 69.0% [62.5, 75.5] | 31.0% [24.5, 37.5] |
| encyclopedic | encyclopedic | 82.0% [76.5, 87.5] | 97.0% [94.5, 99.0] | 3.0% [1.0, 5.5] |

None among all known pairs: 6.4% [5.3, 7.7].

| canonical name | relations | precision among known pairs |
|---|---|---|
| inflection | inflection | 98.1% [96.2, 99.6] |
| derivation | derivation | 58.6% [53.9, 64.0] |
| synonym | synonym | 62.8% [57.5, 68.1] |
| antonym | antonym | 94.7% [91.6, 97.6] |
| hypernym | hypernym | 61.2% [54.1, 68.3] |
| meronym | meronym | 77.1% [71.3, 82.6] |
| co-hyponym | co-hyponym | 75.7% [67.6, 83.6] |
| encyclopedic | encyclopedic | 29.3% [25.7, 32.9] |

Confusion (pairs of each drawn relation given each canonical name; a pair can be given several):

| drawn | pairs | inflection | derivation | synonym | antonym | hypernym | meronym | co-hyponym | encyclopedic | other names only | none |
|---|---|---|---|---|---|---|---|---|---|---|---|
| inflection | 200 | 183 | 85 | 4 | 0 | 0 | 1 | 0 | 18 | 4 | 0 |
| derivation | 200 | 24 | 196 | 3 | 3 | 0 | 1 | 0 | 55 | 0 | 0 |
| synonym | 200 | 2 | 10 | 175 | 0 | 26 | 5 | 5 | 55 | 0 | 4 |
| antonym | 200 | 2 | 24 | 6 | 191 | 1 | 1 | 16 | 14 | 0 | 2 |
| hypernym | 200 | 1 | 4 | 80 | 1 | 90 | 13 | 3 | 71 | 2 | 21 |
| meronym | 200 | 2 | 14 | 16 | 1 | 12 | 143 | 6 | 125 | 1 | 7 |
| co-hyponym | 200 | 0 | 5 | 15 | 7 | 21 | 6 | 66 | 62 | 5 | 62 |
| encyclopedic | 200 | 0 | 17 | 5 | 5 | 33 | 35 | 11 | 164 | 0 | 6 |

## Open subsets

| subset | pairs | with a relation | none | relations per pair | held in a dictionary |
|---|---|---|---|---|---|
| far in both | 2000 | 4.6% [3.8, 5.5] | 95.4% [94.5, 96.2] | 0.051 | 0.0% [0.0, 0.0] |
| near in both | 200 | 73.5% [66.5, 79.0] | 26.5% [21.0, 33.5] | 1.155 | 0.0% [0.0, 0.0] |
| random, no relation | 2000 | 10.5% [9.1, 11.9] | 89.5% [88.0, 90.9] | 0.138 | 0.0% [0.0, 0.0] |
| random, any | 1000 | 10.3% [8.5, 12.2] | 89.7% [87.8, 91.5] | 0.137 | 0.4% [0.1, 0.8] |

Difference of the share with a relation (percentage points, 95% interval): far in both minus random, no relation -5.9 [-7.5, -4.3]; near in both minus random, no relation +63.0 [+57.2, +68.5]; near in both minus far in both +68.9 [+63.0, +74.5]; random, no relation minus random, any +0.2 [-2.1, +2.6]; far in both minus random, any -5.7 [-7.8, -3.6].

## far in both

| relation | pairs | share |
|---|---|---|
| none | 1908 | 95.4% [94.5, 96.2] |
| orthographic | 26 | 1.3% [0.9, 1.8] |
| encyclopedic | 20 | 1.0% [0.5, 1.5] |
| co-hyponym | 9 | 0.4% [0.2, 0.8] |
| same part of speech | 8 | 0.4% [0.1, 0.7] |
| antonym | 6 | 0.3% [0.1, 0.5] |
| compound | 6 | 0.3% [0.1, 0.5] |
| association | 4 | 0.2% [0.1, 0.4] |
| domain | 4 | 0.2% [0.1, 0.4] |
| synonym | 4 | 0.2% [0.1, 0.4] |
| attribute | 3 | 0.1% [0.0, 0.4] |
| function | 3 | 0.1% [0.0, 0.4] |
| phonetic | 3 | 0.1% [0.0, 0.4] |
| derivation | 2 | 0.1% [0.0, 0.2] |
| hypernym | 2 | 0.1% [0.0, 0.2] |
| collocation | 1 | 0.1% [0.0, 0.1] |
| meronym | 1 | 0.1% [0.0, 0.1] |
| translation | 1 | 0.1% [0.0, 0.1] |

### far in both: none (1908), first 40

- branch / quotation (PPMI-SVD -0.156, SGNS -0.129)
- disjunction / subterranean (PPMI-SVD -0.133, SGNS -0.135)
- inflationary / tortured (PPMI-SVD -0.113, SGNS -0.157)
- opera / conditional (PPMI-SVD -0.101, SGNS -0.148)
- australasia / kubrick (PPMI-SVD -0.151, SGNS -0.202)
- offshoot / spacecraft (PPMI-SVD -0.159, SGNS -0.116)
- related / ade (PPMI-SVD -0.097, SGNS -0.141)
- gregory / allowable (PPMI-SVD -0.12, SGNS -0.155)
- robotics / spots (PPMI-SVD -0.163, SGNS -0.122)
- er / centering (PPMI-SVD -0.104, SGNS -0.144)
- round / gifted (PPMI-SVD -0.115, SGNS -0.119)
- skunk / successive (PPMI-SVD -0.163, SGNS -0.14)
- briefly / guideline (PPMI-SVD -0.149, SGNS -0.144)
- zimmer / display (PPMI-SVD -0.123, SGNS -0.151)
- hostility / laboratory (PPMI-SVD -0.139, SGNS -0.136)
- semen / residential (PPMI-SVD -0.109, SGNS -0.112)
- android / consult (PPMI-SVD -0.096, SGNS -0.182)
- surprised / coaxial (PPMI-SVD -0.135, SGNS -0.13)
- club / utilised (PPMI-SVD -0.124, SGNS -0.114)
- boone / unwanted (PPMI-SVD -0.101, SGNS -0.13)
- edgar / aloes (PPMI-SVD -0.135, SGNS -0.103)
- determination / spa (PPMI-SVD -0.101, SGNS -0.127)
- olympiad / hide (PPMI-SVD -0.158, SGNS -0.162)
- theft / tun (PPMI-SVD -0.119, SGNS -0.124)
- cm / dishonest (PPMI-SVD -0.101, SGNS -0.15)
- neutral / sorcerer (PPMI-SVD -0.104, SGNS -0.133)
- sire / yugoslavian (PPMI-SVD -0.106, SGNS -0.174)
- deaf / elasticity (PPMI-SVD -0.119, SGNS -0.113)
- encroachment / fr (PPMI-SVD -0.102, SGNS -0.106)
- yes / yorktown (PPMI-SVD -0.119, SGNS -0.148)
- nineteenth / farad (PPMI-SVD -0.141, SGNS -0.149)
- lisbon / whip (PPMI-SVD -0.119, SGNS -0.124)
- latin / gale (PPMI-SVD -0.126, SGNS -0.115)
- discredited / krishna (PPMI-SVD -0.152, SGNS -0.183)
- privately / midpoint (PPMI-SVD -0.096, SGNS -0.139)
- contemporaries / redirect (PPMI-SVD -0.1, SGNS -0.131)
- space / faux (PPMI-SVD -0.121, SGNS -0.108)
- nb / retaliation (PPMI-SVD -0.169, SGNS -0.177)
- territorial / copycat (PPMI-SVD -0.114, SGNS -0.142)
- soviets / tarot (PPMI-SVD -0.113, SGNS -0.122)

### far in both: orthographic (26)

- noel / cords (PPMI-SVD -0.122, SGNS -0.11): anagram
- kalashnikov / o (PPMI-SVD -0.12, SGNS -0.103): both contain the letter o, o is a letter in kalashnikov
- ontario / decryption (PPMI-SVD -0.108, SGNS -0.143): both contain the letter i, both contain the letter n, both contain the letter o, both contain the letter r, both contain the letter t
- shamanism / westminster (PPMI-SVD -0.153, SGNS -0.108): both contain the letter i, both contain the letter m, both contain the letter n, both contain the letter s
- armageddon / educate (PPMI-SVD -0.12, SGNS -0.113): both contain the letter a, both contain the letter d, both contain the letter e
- joint / stratified (PPMI-SVD -0.113, SGNS -0.173): both contain the letter i, both contain the letter t
- abort / today (PPMI-SVD -0.125, SGNS -0.136): both contain the letter a, both contain the letter d, both contain the letter o
- oration / aloe (PPMI-SVD -0.118, SGNS -0.12): anagram_pair_letters_shared
- masses / masquerade (PPMI-SVD -0.116, SGNS -0.112): shared prefix 'mas'
- queer / order (PPMI-SVD -0.162, SGNS -0.182): same ending (-er)
- odor / orient (PPMI-SVD -0.098, SGNS -0.126): anagram-like letter overlap
- gale / gallic (PPMI-SVD -0.137, SGNS -0.124): shared prefix 'gal'
- perplexed / increased (PPMI-SVD -0.126, SGNS -0.106): both_end_in_ed
- lithium / goliath (PPMI-SVD -0.107, SGNS -0.106): shared_letters_l_i_t_h
- em / turkestan (PPMI-SVD -0.129, SGNS -0.126): turkestan contains the letters 'e' 'm'? no
- odour / dover (PPMI-SVD -0.122, SGNS -0.141): same length
- minimum / mischievous (PPMI-SVD -0.215, SGNS -0.149): alliteration, same initial letters
- services / savage (PPMI-SVD -0.101, SGNS -0.104): same initial letter
- lien / resilient (PPMI-SVD -0.107, SGNS -0.18): substring
- praetor / h (PPMI-SVD -0.096, SGNS -0.188): contains letter
- bounty / boundary (PPMI-SVD -0.131, SGNS -0.157): orthographic_similarity, shared_prefix_boun
- based / ambassador (PPMI-SVD -0.109, SGNS -0.107): anagram_substring
- accidental / accra (PPMI-SVD -0.131, SGNS -0.222): shared_initial_letters
- irony / iis (PPMI-SVD -0.135, SGNS -0.104): anagram-like letter overlap (irony contains i, iis is made of i and s)
- expedition / embedded (PPMI-SVD -0.108, SGNS -0.121): same_first_letter
- aloe / allotted (PPMI-SVD -0.113, SGNS -0.162): alliteration

### far in both: encyclopedic (20)

- association / stylistic (PPMI-SVD -0.141, SGNS -0.105): related_to
- frost / colombo (PPMI-SVD -0.097, SGNS -0.112): related_to
- luggage / calculus (PPMI-SVD -0.115, SGNS -0.107): stone
- elements / lighthouse (PPMI-SVD -0.097, SGNS -0.105): related_to
- intercourse / deluxe (PPMI-SVD -0.103, SGNS -0.107): place names in pennsylvania (intercourse, pa)
- reflecting / equus (PPMI-SVD -0.145, SGNS -0.132): equus (play by peter shaffer)
- tip / public (PPMI-SVD -0.103, SGNS -0.139): tipping_in_public_service
- sentiment / ceo (PPMI-SVD -0.097, SGNS -0.178): investor sentiment toward ceo
- browning / colors (PPMI-SVD -0.102, SGNS -0.114): browning is a color change, browning is a process that produces colors, browning is a surname
- galton / police (PPMI-SVD -0.123, SGNS -0.119): related_to
- write / beech (PPMI-SVD -0.101, SGNS -0.129): etymology: 'book' derives from germanic word for beech, on whose wood runes were written
- epic / wrongdoing (PPMI-SVD -0.124, SGNS -0.145): common_story_theme
- boxer / festive (PPMI-SVD -0.126, SGNS -0.143): boxing day
- grease / clarify (PPMI-SVD -0.102, SGNS -0.179): butter
- literature / intruder (PPMI-SVD -0.098, SGNS -0.143): the intruder: title of literary works (maeterlinck play, borges story, faulkner's intruder in the dust)
- monarch / cheyenne (PPMI-SVD -0.1, SGNS -0.105): both are words tied to american place and animal names, both have helicopter namesakes (bell cheyenne / monarch aircraft naming)
- ottoman / sire (PPMI-SVD -0.115, SGNS -0.13): ottoman_sultan_addressed_as_sire
- equus / flare (PPMI-SVD -0.098, SGNS -0.111): flehmen response
- elimination / hearse (PPMI-SVD -0.118, SGNS -0.142): death association
- preamble / leading (PPMI-SVD -0.192, SGNS -0.128): attribute, related_to

### far in both: co-hyponym (9)

- bush / coexist (PPMI-SVD -0.119, SGNS -0.133): 'coexist' bumper sticker vs. bush political bumper stickers
- pronounced / ethnographic (PPMI-SVD -0.156, SGNS -0.111): both adjectives
- fascinating / iraqi (PPMI-SVD -0.1, SGNS -0.184): both adjectives
- dress / kohl (PPMI-SVD -0.147, SGNS -0.106): cosmetic_vs_clothing
- weeds / olympic (PPMI-SVD -0.125, SGNS -0.14): weeds and olympic are both 2000s us tv/media proper nouns
- medial / wonderful (PPMI-SVD -0.127, SGNS -0.118): both adjectives
- altruistic / tenth (PPMI-SVD -0.151, SGNS -0.109): both adjectives
- undesirable / pontifical (PPMI-SVD -0.137, SGNS -0.112): both adjectives
- agate / second (PPMI-SVD -0.108, SGNS -0.128): both are units of type size (agate line / second)

### far in both: same part of speech (8)

- participatory / destitute (PPMI-SVD -0.097, SGNS -0.16): both_adjectives
- perplexed / increased (PPMI-SVD -0.126, SGNS -0.106): both_past_participle_forms
- golden / anxious (PPMI-SVD -0.132, SGNS -0.116): both_adjectives
- galilean / rusty (PPMI-SVD -0.112, SGNS -0.116): both_adjectives
- restless / valid (PPMI-SVD -0.105, SGNS -0.141): both_adjectives
- randomized / adjective (PPMI-SVD -0.107, SGNS -0.142): part_of_speech
- boise / rommel (PPMI-SVD -0.117, SGNS -0.124): both proper nouns
- graduated / resolving (PPMI-SVD -0.11, SGNS -0.116): both_past_or_participle_forms

### far in both: antonym (6)

- official / unconventional (PPMI-SVD -0.099, SGNS -0.119): antonym
- wilt / stability (PPMI-SVD -0.147, SGNS -0.129): antonym
- revolution / reserved (PPMI-SVD -0.102, SGNS -0.118): contrast
- relief / dent (PPMI-SVD -0.12, SGNS -0.153): antonym
- educated / dummy (PPMI-SVD -0.121, SGNS -0.236): antonym
- planned / undetermined (PPMI-SVD -0.133, SGNS -0.112): antonym

### far in both: compound (6)

- code / sweating (PPMI-SVD -0.157, SGNS -0.108): phrase component, phrase: code sweating
- class / drilled (PPMI-SVD -0.11, SGNS -0.118): collocation
- association / stylistic (PPMI-SVD -0.141, SGNS -0.105): collocation
- false / auspices (PPMI-SVD -0.101, SGNS -0.147): collocation
- vacancy / published (PPMI-SVD -0.101, SGNS -0.122): collocation
- debussy / reduce (PPMI-SVD -0.141, SGNS -0.133): piano reduction

### far in both: association (4)

- intercourse / deluxe (PPMI-SVD -0.103, SGNS -0.107): sexual connotation
- tip / public (PPMI-SVD -0.103, SGNS -0.139): public_tip_off
- startup / bearded (PPMI-SVD -0.142, SGNS -0.193): stereotype of startup founders
- vice / impure (PPMI-SVD -0.127, SGNS -0.14): related_moral_concept

### far in both: domain (4)

- joint / stratified (PPMI-SVD -0.113, SGNS -0.173): joint and stratified are both geology terms, joint and stratified are both statistics terms (joint distribution, stratified sampling)
- sentiment / ceo (PPMI-SVD -0.097, SGNS -0.178): business context
- tack / near (PPMI-SVD -0.123, SGNS -0.174): sailing terms
- ottoman / sire (PPMI-SVD -0.115, SGNS -0.13): royal_title_context

### far in both: synonym (4)

- bum / subsequent (PPMI-SVD -0.121, SGNS -0.114): shared synonym (behind), shared synonym (posterior)
- posture / station (PPMI-SVD -0.115, SGNS -0.109): synonym
- man / oversee (PPMI-SVD -0.112, SGNS -0.107): synonym
- vice / impure (PPMI-SVD -0.127, SGNS -0.14): semantic_similarity

### far in both: attribute (3)

- round / aten (PPMI-SVD -0.136, SGNS -0.138): shape (aten is depicted as a round sun disk)
- dress / kohl (PPMI-SVD -0.147, SGNS -0.106): related_to_appearance
- flaw / youth (PPMI-SVD -0.132, SGNS -0.104): youthful flaw (immaturity)

### far in both: function (3)

- attest / chair (PPMI-SVD -0.099, SGNS -0.112): chair can attest as an official
- swelling / rn (PPMI-SVD -0.154, SGNS -0.15): nurse (rn) assesses swelling
- rip / commemorating (PPMI-SVD -0.118, SGNS -0.143): rip_used_in_commemorating_dead

### far in both: phonetic (3)

- anathema / montana (PPMI-SVD -0.157, SGNS -0.156): rhyme
- fraternal / visual (PPMI-SVD -0.197, SGNS -0.148): rhyme
- odour / dover (PPMI-SVD -0.122, SGNS -0.141): slant rhyme

### far in both: derivation (2)

- instigation / regression (PPMI-SVD -0.106, SGNS -0.139): shared suffix -ion
- smoother / sawyer (PPMI-SVD -0.151, SGNS -0.122): agent noun

### far in both: hypernym (2)

- tagore / entity (PPMI-SVD -0.099, SGNS -0.113): hypernym, instance_of
- tinker / human (PPMI-SVD -0.122, SGNS -0.108): is_a

### far in both: collocation (1)

- walk / piracy (PPMI-SVD -0.102, SGNS -0.158): walk the plank

### far in both: meronym (1)

- elements / lighthouse (PPMI-SVD -0.097, SGNS -0.105): has_part, part_of

### far in both: translation (1)

- steinbeck / cairn (PPMI-SVD -0.117, SGNS -0.139): stone etymology (stein = stone; cairn = stone pile)

## near in both

| relation | pairs | share |
|---|---|---|
| encyclopedic | 65 | 32.5% [26.0, 39.0] |
| none | 53 | 26.5% [21.0, 33.5] |
| domain | 42 | 21.0% [15.5, 27.5] |
| co-hyponym | 37 | 18.5% [13.0, 24.0] |
| compound | 16 | 8.0% [4.5, 12.0] |
| hypernym | 10 | 5.0% [2.0, 8.0] |
| derivation | 8 | 4.0% [1.5, 7.0] |
| function | 8 | 4.0% [1.5, 7.0] |
| antonym | 7 | 3.5% [1.0, 6.0] |
| association | 7 | 3.5% [1.5, 6.5] |
| meronym | 7 | 3.5% [1.5, 6.0] |
| attribute | 5 | 2.5% [0.5, 5.0] |
| collocation | 4 | 2.0% [0.5, 4.0] |
| orthographic | 4 | 2.0% [0.5, 4.0] |
| same part of speech | 4 | 2.0% [0.5, 4.5] |
| synonym | 4 | 2.0% [0.5, 4.0] |
| phonetic | 2 | 1.0% [0.0, 2.5] |
| sequence | 1 | 0.5% [0.0, 1.5] |

### near in both: encyclopedic (65)

- certainty / understand (PPMI-SVD 0.464, SGNS 0.41): related_to
- gamut / cyan (PPMI-SVD 0.482, SGNS 0.453): related_to
- sayers / murphy (PPMI-SVD 0.518, SGNS 0.441): surnames
- selenium / phosphate (PPMI-SVD 0.59, SGNS 0.435): both found in fertilizers and soil
- federally / state (PPMI-SVD 0.467, SGNS 0.445): related_concept
- glycine / cytochrome (PPMI-SVD 0.661, SGNS 0.565): related_to
- monsoon / storm (PPMI-SVD 0.504, SGNS 0.429): related_to
- monotheistic / tenet (PPMI-SVD 0.693, SGNS 0.493): related_to
- nullification / condemnation (PPMI-SVD 0.474, SGNS 0.457): related concept
- perfection / knowledge (PPMI-SVD 0.521, SGNS 0.497): related_to
- shortstop / milwaukee (PPMI-SVD 0.593, SGNS 0.488): baseball (milwaukee brewers have a shortstop)
- ecuador / columbian (PPMI-SVD 0.512, SGNS 0.443): geographic neighbor (ecuador borders colombia), shared history (gran colombia)
- mycenaean / inscription (PPMI-SVD 0.575, SGNS 0.452): related_to
- cardinality / measurable (PPMI-SVD 0.847, SGNS 0.574): related_concept
- methodology / algorithmic (PPMI-SVD 0.546, SGNS 0.518): topical association
- discomfort / heart (PPMI-SVD 0.512, SGNS 0.446): chest pain symptom
- taped / tv (PPMI-SVD 0.44, SGNS 0.449): related_to
- ethnically / sardinian (PPMI-SVD 0.532, SGNS 0.411): related_to
- sperm / mating (PPMI-SVD 0.665, SGNS 0.537): related_to
- enactment / laws (PPMI-SVD 0.628, SGNS 0.539): related_to
- cheerful / smile (PPMI-SVD 0.457, SGNS 0.424): causes, has_property, related_to
- handball / champion (PPMI-SVD 0.599, SGNS 0.462): topical association
- hermitage / guggenheim (PPMI-SVD 0.516, SGNS 0.443): both have branches in multiple cities (guggenheim hermitage museum in las vegas)
- faith / sacrament (PPMI-SVD 0.666, SGNS 0.535): related_to
- sensory / consciousness (PPMI-SVD 0.655, SGNS 0.644): related_to
- speak / think (PPMI-SVD 0.46, SGNS 0.433): related_to
- acadian / alberta (PPMI-SVD 0.455, SGNS 0.517): both relate to canada
- witty / memorable (PPMI-SVD 0.553, SGNS 0.473): related_to
- walloon / holland (PPMI-SVD 0.459, SGNS 0.487): geographic proximity
- anderson / american (PPMI-SVD 0.513, SGNS 0.505): related_to
- manifesto / stalinism (PPMI-SVD 0.55, SGNS 0.477): related_to
- parliamentary / convene (PPMI-SVD 0.589, SGNS 0.427): related_to
- identifier / browser (PPMI-SVD 0.471, SGNS 0.583): related_to
- cinnamon / candy (PPMI-SVD 0.557, SGNS 0.408): cinnamon_candy_compound
- runner / kick (PPMI-SVD 0.61, SGNS 0.408): related_to
- percussion / harpsichord (PPMI-SVD 0.685, SGNS 0.554): related_to
- gdp / privatization (PPMI-SVD 0.548, SGNS 0.457): related_to
- biographical / textual (PPMI-SVD 0.499, SGNS 0.398): related_to
- moral / legal (PPMI-SVD 0.445, SGNS 0.502): related_concept
- convince / willingness (PPMI-SVD 0.438, SGNS 0.402): causes
- sikhism / madras (PPMI-SVD 0.482, SGNS 0.424): associated_with_india
- melt / soaked (PPMI-SVD 0.469, SGNS 0.463): both relate to liquid/water
- bicarbonate / sulfuric (PPMI-SVD 0.858, SGNS 0.673): both relate to sulfur/carbon oxyacid salts and acids, chemical reaction (sodium bicarbonate neutralizes sulfuric acid)
- hugo / prize (PPMI-SVD 0.67, SGNS 0.459): hugo award
- cretaceous / glaciation (PPMI-SVD 0.737, SGNS 0.617): both relate to earth's climate history
- pastor / anabaptist (PPMI-SVD 0.644, SGNS 0.482): related_to
- coordinator / ceo (PPMI-SVD 0.442, SGNS 0.432): related_to
- dysfunction / anxiety (PPMI-SVD 0.687, SGNS 0.62): related_to
- domain / document (PPMI-SVD 0.45, SGNS 0.4): related_to
- pennant / pitching (PPMI-SVD 0.744, SGNS 0.627): related_to
- elector / linz (PPMI-SVD 0.538, SGNS 0.476): related_to
- catholicism / christ (PPMI-SVD 0.523, SGNS 0.476): related_to
- rowan / patrick (PPMI-SVD 0.591, SGNS 0.473): both_irish_associated
- anne / anjou (PPMI-SVD 0.521, SGNS 0.429): anne of anjou, historical title
- rhythm / style (PPMI-SVD 0.535, SGNS 0.476): related_to
- stimulant / dea (PPMI-SVD 0.644, SGNS 0.424): controlled_substance_enforcement
- mono / channels (PPMI-SVD 0.488, SGNS 0.424): audio channel configuration (mono = one channel)
- checkers / tile (PPMI-SVD 0.643, SGNS 0.496): checkerboard_pattern
- mandate / intervention (PPMI-SVD 0.446, SGNS 0.425): related_to
- aeneas / ovid (PPMI-SVD 0.605, SGNS 0.535): character_in_work_of, related_to
- stimulus / dependence (PPMI-SVD 0.496, SGNS 0.418): dependent variable (response depends on stimulus)
- psyche / passion (PPMI-SVD 0.479, SGNS 0.474): related_to
- imprisonment / committed (PPMI-SVD 0.706, SGNS 0.529): related_to
- appointed / supervision (PPMI-SVD 0.452, SGNS 0.444): related_concept
- airline / airfield (PPMI-SVD 0.532, SGNS 0.401): related_to

### near in both: none (53), first 40

- essay / spenser (PPMI-SVD 0.463, SGNS 0.466)
- organizational / enhance (PPMI-SVD 0.502, SGNS 0.409)
- hardened / thin (PPMI-SVD 0.469, SGNS 0.424)
- nanny / protagonist (PPMI-SVD 0.555, SGNS 0.45)
- empiricism / rhetoric (PPMI-SVD 0.436, SGNS 0.433)
- cause / prolonged (PPMI-SVD 0.6, SGNS 0.559)
- epidemiology / hyperthyroidism (PPMI-SVD 0.544, SGNS 0.504)
- threaded / byte (PPMI-SVD 0.452, SGNS 0.515)
- arid / extremity (PPMI-SVD 0.47, SGNS 0.43)
- habitable / horizon (PPMI-SVD 0.511, SGNS 0.427)
- insecticide / viral (PPMI-SVD 0.512, SGNS 0.409)
- implemented / package (PPMI-SVD 0.501, SGNS 0.476)
- chorale / goethe (PPMI-SVD 0.46, SGNS 0.428)
- vertical / crest (PPMI-SVD 0.441, SGNS 0.448)
- concentric / anisotropic (PPMI-SVD 0.44, SGNS 0.434)
- retaliation / brutally (PPMI-SVD 0.446, SGNS 0.429)
- robin / glen (PPMI-SVD 0.704, SGNS 0.504)
- conception / kabbalah (PPMI-SVD 0.512, SGNS 0.429)
- stardom / duo (PPMI-SVD 0.442, SGNS 0.444)
- moniker / dynamite (PPMI-SVD 0.621, SGNS 0.414)
- depend / compensate (PPMI-SVD 0.453, SGNS 0.444)
- insane / suffering (PPMI-SVD 0.441, SGNS 0.546)
- characteristically / timbre (PPMI-SVD 0.463, SGNS 0.415)
- dignity / absolutism (PPMI-SVD 0.585, SGNS 0.437)
- notorious / bloody (PPMI-SVD 0.444, SGNS 0.442)
- heartbeat / nipple (PPMI-SVD 0.449, SGNS 0.399)
- graphically / blackboard (PPMI-SVD 0.514, SGNS 0.434)
- vacuum / inductor (PPMI-SVD 0.713, SGNS 0.545)
- mate / kangaroo (PPMI-SVD 0.527, SGNS 0.444)
- pilate / witness (PPMI-SVD 0.445, SGNS 0.404)
- proscribed / oligarchy (PPMI-SVD 0.503, SGNS 0.405)
- wicked / jesus (PPMI-SVD 0.505, SGNS 0.407)
- comprehensive / foundation (PPMI-SVD 0.479, SGNS 0.481)
- caspar / mathematician (PPMI-SVD 0.592, SGNS 0.477)
- unprecedented / liberalization (PPMI-SVD 0.478, SGNS 0.417)
- nigger / angry (PPMI-SVD 0.548, SGNS 0.496)
- inconsistent / prove (PPMI-SVD 0.548, SGNS 0.41)
- maoist / malayan (PPMI-SVD 0.437, SGNS 0.472)
- northward / rift (PPMI-SVD 0.71, SGNS 0.51)
- malawi / bioko (PPMI-SVD 0.473, SGNS 0.485)

### near in both: domain (42)

- gamut / cyan (PPMI-SVD 0.482, SGNS 0.453): color_domain
- episcopalian / jehovah (PPMI-SVD 0.526, SGNS 0.406): religious_context
- untreated / coronary (PPMI-SVD 0.743, SGNS 0.448): medical terms, untreated coronary artery disease
- selenium / phosphate (PPMI-SVD 0.59, SGNS 0.435): both chemistry terms
- geometrically / scalar (PPMI-SVD 0.463, SGNS 0.5): related_domain
- penitent / martyrdom (PPMI-SVD 0.526, SGNS 0.501): related_domain
- chop / lettuce (PPMI-SVD 0.558, SGNS 0.417): food preparation
- mycenaean / inscription (PPMI-SVD 0.575, SGNS 0.452): topical_association
- cardinality / measurable (PPMI-SVD 0.847, SGNS 0.574): mathematical_property
- sentence / pleading (PPMI-SVD 0.531, SGNS 0.455): court proceedings, legal terms
- detachment / military (PPMI-SVD 0.496, SGNS 0.425): domain
- superposition / arbitrary (PPMI-SVD 0.471, SGNS 0.443): mathematical_term
- phenylalanine / lactic (PPMI-SVD 0.739, SGNS 0.65): related to metabolism
- payload / lm (PPMI-SVD 0.631, SGNS 0.499): spaceflight context (lm = lunar module, carried as a payload)
- physics / inertial (PPMI-SVD 0.495, SGNS 0.404): domain_term, topical_association
- baldwin / empress (PPMI-SVD 0.683, SGNS 0.436): royalty
- fresco / paleolithic (PPMI-SVD 0.448, SGNS 0.464): art_history
- trail / glen (PPMI-SVD 0.46, SGNS 0.411): hiking_terrain_context
- addiction / obsessive (PPMI-SVD 0.713, SGNS 0.489): both psychological terms
- faith / sacrament (PPMI-SVD 0.666, SGNS 0.535): religious_concept
- sensory / consciousness (PPMI-SVD 0.655, SGNS 0.644): semantic_field
- research / developmental (PPMI-SVD 0.511, SGNS 0.46): topical_association
- amphibious / artillery (PPMI-SVD 0.596, SGNS 0.527): military_domain
- executable / dump (PPMI-SVD 0.552, SGNS 0.435): computing domain
- gdp / privatization (PPMI-SVD 0.548, SGNS 0.457): economics domain
- regression / likelihood (PPMI-SVD 0.609, SGNS 0.529): maximum_likelihood_estimation, statistics_terms
- cognate / altaic (PPMI-SVD 0.529, SGNS 0.421): linguistics_domain
- joule / entropy (PPMI-SVD 0.589, SGNS 0.51): same_domain_thermodynamics
- cretaceous / glaciation (PPMI-SVD 0.737, SGNS 0.617): both geological terms
- pastor / anabaptist (PPMI-SVD 0.644, SGNS 0.482): religious_context
- excalibur / balder (PPMI-SVD 0.455, SGNS 0.416): mythology
- scaling / trigonometric (PPMI-SVD 0.695, SGNS 0.435): mathematical_terms
- pennant / pitching (PPMI-SVD 0.744, SGNS 0.627): context_baseball
- gunnery / commander (PPMI-SVD 0.541, SGNS 0.493): military_domain, semantic_field
- mapping / interval (PPMI-SVD 0.542, SGNS 0.419): co-occurrence in mathematics, interval mapping (genetics)
- rhythm / style (PPMI-SVD 0.535, SGNS 0.476): music_term
- trauma / pulmonary (PPMI-SVD 0.685, SGNS 0.531): medical terms
- chord / orchestral (PPMI-SVD 0.618, SGNS 0.498): shared domain: music
- meiosis / gene (PPMI-SVD 0.692, SGNS 0.559): genetics domain
- monomer / heme (PPMI-SVD 0.673, SGNS 0.562): biochemistry domain
- partake / supper (PPMI-SVD 0.621, SGNS 0.47): eating
- municipal / cabinet (PPMI-SVD 0.442, SGNS 0.416): government_related

### near in both: co-hyponym (37)

- episcopalian / jehovah (PPMI-SVD 0.526, SGNS 0.406): christian_denominations
- utrecht / bavaria (PPMI-SVD 0.503, SGNS 0.408): both_european_regions
- aquarium / bird (PPMI-SVD 0.521, SGNS 0.503): co-hypernym
- sinatra / loren (PPMI-SVD 0.46, SGNS 0.428): both singers/actors of the same era, both surnames of italian-heritage entertainers (frank sinatra, sophia loren)
- clement / dominic (PPMI-SVD 0.586, SGNS 0.41): both_given_names, both_papal_names, both_saint_names
- nullification / condemnation (PPMI-SVD 0.474, SGNS 0.457): both legal/judicial acts
- fetal / puberty (PPMI-SVD 0.583, SGNS 0.578): both precede adulthood
- ecuador / columbian (PPMI-SVD 0.512, SGNS 0.443): both south american
- jung / ernst (PPMI-SVD 0.599, SGNS 0.415): both german-language surnames, both surnames of 20th-century figures linked to psychology and surrealist art (carl jung, max ernst)
- overly / equally (PPMI-SVD 0.495, SGNS 0.469): degree_modifier
- phenylalanine / lactic (PPMI-SVD 0.739, SGNS 0.65): biochemical compounds
- summation / calculating (PPMI-SVD 0.583, SGNS 0.426): both are arithmetic operations
- trail / glen (PPMI-SVD 0.46, SGNS 0.411): landscape_features
- hermitage / guggenheim (PPMI-SVD 0.516, SGNS 0.443): both art museums, hermitage is in st. petersburg, guggenheim is in new york
- netscape / acrobat (PPMI-SVD 0.682, SGNS 0.524): adobe acrobat vs netscape navigator: 1990s internet-era software, software products, web/document software
- speak / think (PPMI-SVD 0.46, SGNS 0.433): cognitive_and_communicative_acts
- curd / minestrone (PPMI-SVD 0.533, SGNS 0.44): both_foods
- herodotus / pliny (PPMI-SVD 0.807, SGNS 0.575): both ancient historians/writers, both classical authors, co-hyponyms
- walloon / holland (PPMI-SVD 0.459, SGNS 0.487): co-hyponyms (low countries regions)
- pentecostal / lutheranism (PPMI-SVD 0.875, SGNS 0.535): both protestant christian denominations, co-hyponyms
- dionysius / ignatius (PPMI-SVD 0.565, SGNS 0.466): both greek-origin given names, both names of early church fathers, both names of popes, co-hyponyms (saints' names)
- percussion / harpsichord (PPMI-SVD 0.685, SGNS 0.554): both are musical instrument categories
- biographical / textual (PPMI-SVD 0.499, SGNS 0.398): both adjectives, co-hyponyms (types of scholarly analysis or criticism)
- moral / legal (PPMI-SVD 0.445, SGNS 0.502): co-hyponym
- vocational / undergraduate (PPMI-SVD 0.836, SGNS 0.501): co-hyponyms (types of education)
- blasphemy / perjury (PPMI-SVD 0.712, SGNS 0.499): both involve false or irreverent speech, both offenses, co-hyponyms
- neuter / genitive (PPMI-SVD 0.944, SGNS 0.643): co-hyponyms (grammatical categories)
- coordinator / ceo (PPMI-SVD 0.442, SGNS 0.432): co-hyponym
- volcanic / sedimentary (PPMI-SVD 0.714, SGNS 0.617): co-hyponyms
- liberian / fiji (PPMI-SVD 0.574, SGNS 0.559): pacific_and_africa_nations_cotype
- rowan / patrick (PPMI-SVD 0.591, SGNS 0.473): both_given_names
- cardiff / surrey (PPMI-SVD 0.74, SGNS 0.438): both places in great britain
- bahamian / lesotho (PPMI-SVD 0.468, SGNS 0.472): both commonwealth members, both former british territories, both nationality/country names
- marsh / palmer (PPMI-SVD 0.502, SGNS 0.456): both surnames
- honey / cider (PPMI-SVD 0.638, SGNS 0.481): both are sweet, both are used to make fermented drinks (mead, hard cider)
- sax / percussion (PPMI-SVD 0.681, SGNS 0.512): co-hyponyms (both musical instruments), contrast (wind vs percussion instrument family)
- confucian / tibetan (PPMI-SVD 0.591, SGNS 0.497): both asian cultural adjectives, both religious/philosophical traditions

### near in both: compound (16)

- enforced / governmental (PPMI-SVD 0.497, SGNS 0.412): collocation
- discomfort / heart (PPMI-SVD 0.512, SGNS 0.446): heartache, heartburn
- hiding / wounded (PPMI-SVD 0.549, SGNS 0.435): co-occurrence
- scholarship / biblical (PPMI-SVD 0.55, SGNS 0.504): collocation
- yes / go (PPMI-SVD 0.516, SGNS 0.417): collocation
- research / developmental (PPMI-SVD 0.511, SGNS 0.46): collocation
- parliamentary / convene (PPMI-SVD 0.589, SGNS 0.427): co-occurrence
- cinnamon / candy (PPMI-SVD 0.557, SGNS 0.408): co-occurrence
- subway / decker (PPMI-SVD 0.701, SGNS 0.398): compound_word_completion
- adjustment / gradual (PPMI-SVD 0.504, SGNS 0.41): collocation
- egalitarian / radical (PPMI-SVD 0.539, SGNS 0.402): co-occurrence
- hugo / prize (PPMI-SVD 0.67, SGNS 0.459): collocation
- dysfunction / anxiety (PPMI-SVD 0.687, SGNS 0.62): co-occurrence
- mall / sprawling (PPMI-SVD 0.48, SGNS 0.513): collocation
- easy / relatively (PPMI-SVD 0.454, SGNS 0.536): collocation
- imprisonment / committed (PPMI-SVD 0.706, SGNS 0.529): co-occurrence

### near in both: hypernym (10)

- monsoon / storm (PPMI-SVD 0.504, SGNS 0.429): hypernym
- hexagonal / octahedron (PPMI-SVD 0.859, SGNS 0.661): geometric_shape_category
- detachment / military (PPMI-SVD 0.496, SGNS 0.425): hypernym
- summation / calculating (PPMI-SVD 0.583, SGNS 0.426): summation is a kind of calculating
- cheerful / smile (PPMI-SVD 0.457, SGNS 0.424): manner_of
- quartz / gemstone (PPMI-SVD 0.632, SGNS 0.493): hypernym, is_a
- percussion / harpsichord (PPMI-SVD 0.685, SGNS 0.554): harpsichord is a keyboard instrument sometimes classified as percussion (struck/plucked by mechanism)
- corporation / toyota (PPMI-SVD 0.485, SGNS 0.411): hypernym, instance_of
- ketamine / anaesthetic (PPMI-SVD 0.797, SGNS 0.678): hypernym, is_a
- honey / cider (PPMI-SVD 0.638, SGNS 0.481): honey cider is a drink

### near in both: derivation (8)

- federally / state (PPMI-SVD 0.467, SGNS 0.445): derivationally_related
- nullification / condemnation (PPMI-SVD 0.474, SGNS 0.457): shared suffix -ation
- overly / equally (PPMI-SVD 0.495, SGNS 0.469): adverb, suffix_ly
- enactment / laws (PPMI-SVD 0.628, SGNS 0.539): derivationally_related
- physics / inertial (PPMI-SVD 0.495, SGNS 0.404): derivationally_related_concept
- buying / buyer (PPMI-SVD 0.617, SGNS 0.484): derivationally_related
- liberian / fiji (PPMI-SVD 0.574, SGNS 0.559): demonym_and_country
- catholicism / christ (PPMI-SVD 0.523, SGNS 0.476): derived_from_belief_in

### near in both: function (8)

- chop / lettuce (PPMI-SVD 0.558, SGNS 0.417): action-object
- sperm / mating (PPMI-SVD 0.665, SGNS 0.537): used_in
- buying / buyer (PPMI-SVD 0.617, SGNS 0.484): agent_of_action
- speak / think (PPMI-SVD 0.46, SGNS 0.433): speak_expresses_thought
- ketamine / anaesthetic (PPMI-SVD 0.797, SGNS 0.678): used_as
- stimulant / dea (PPMI-SVD 0.644, SGNS 0.424): regulated_by
- meiosis / gene (PPMI-SVD 0.692, SGNS 0.559): meiosis passes on genes, meiosis shuffles genes (recombination)
- airline / airfield (PPMI-SVD 0.532, SGNS 0.401): used_by_airlines

### near in both: antonym (7)

- literal / metaphor (PPMI-SVD 0.507, SGNS 0.475): antonym, contrast
- confident / dismay (PPMI-SVD 0.56, SGNS 0.467): contrasting emotional states
- moral / legal (PPMI-SVD 0.445, SGNS 0.502): contrast
- bicarbonate / sulfuric (PPMI-SVD 0.858, SGNS 0.673): acid-base pair
- axiom / fallacious (PPMI-SVD 0.624, SGNS 0.475): contrast
- volcanic / sedimentary (PPMI-SVD 0.714, SGNS 0.617): contrast
- similar / separate (PPMI-SVD 0.502, SGNS 0.586): antonym

### near in both: association (7)

- certainty / understand (PPMI-SVD 0.464, SGNS 0.41): semantic_association
- introduce / adopt (PPMI-SVD 0.674, SGNS 0.573): related_concepts
- feed / nursery (PPMI-SVD 0.444, SGNS 0.451): related_context
- summation / calculating (PPMI-SVD 0.583, SGNS 0.426): semantic relatedness
- addiction / obsessive (PPMI-SVD 0.713, SGNS 0.489): related concepts
- crossed / invasion (PPMI-SVD 0.449, SGNS 0.439): semantic_association
- egalitarian / radical (PPMI-SVD 0.539, SGNS 0.402): related_political_ideology

### near in both: meronym (7)

- gamut / cyan (PPMI-SVD 0.482, SGNS 0.453): part_of
- detachment / military (PPMI-SVD 0.496, SGNS 0.425): part_of
- sperm / mating (PPMI-SVD 0.665, SGNS 0.537): part_of_process
- cinnamon / candy (PPMI-SVD 0.557, SGNS 0.408): ingredient_of
- joule / entropy (PPMI-SVD 0.589, SGNS 0.51): unit_of_component
- monomer / heme (PPMI-SVD 0.673, SGNS 0.562): heme is a part of hemoglobin, whose subunits are monomers
- checkers / tile (PPMI-SVD 0.643, SGNS 0.496): board_game_component

### near in both: attribute (5)

- addiction / obsessive (PPMI-SVD 0.713, SGNS 0.489): addiction can be obsessive, compulsive behavior
- cinnamon / candy (PPMI-SVD 0.557, SGNS 0.408): flavor_of
- stiff / molded (PPMI-SVD 0.543, SGNS 0.413): related property (molded materials become stiff when set)
- checkers / tile (PPMI-SVD 0.643, SGNS 0.496): square_shape
- honey / cider (PPMI-SVD 0.638, SGNS 0.481): same color (amber)

### near in both: collocation (4)

- chop / lettuce (PPMI-SVD 0.558, SGNS 0.417): verb-object collocation
- mycenaean / inscription (PPMI-SVD 0.575, SGNS 0.452): co_occurrence
- executable / dump (PPMI-SVD 0.552, SGNS 0.435): co-occurrence (core dump of an executable)
- partake / supper (PPMI-SVD 0.621, SGNS 0.47): verb-object

### near in both: orthographic (4)

- bats / basal (PPMI-SVD 0.52, SGNS 0.423): anagram
- ecuador / columbian (PPMI-SVD 0.512, SGNS 0.443): common misspelling (columbian for colombian)
- sorry / silly (PPMI-SVD 0.48, SGNS 0.454): same_ending, same_initial_letter, same_length
- airline / airfield (PPMI-SVD 0.532, SGNS 0.401): shared_prefix_air

### near in both: same part of speech (4)

- reckless / mischievous (PPMI-SVD 0.577, SGNS 0.396): both_adjectives
- hermitage / guggenheim (PPMI-SVD 0.516, SGNS 0.443): both proper nouns
- speak / think (PPMI-SVD 0.46, SGNS 0.433): both_verbs
- melt / soaked (PPMI-SVD 0.469, SGNS 0.463): both past participles (melted/soaked)

### near in both: synonym (4)

- reckless / mischievous (PPMI-SVD 0.577, SGNS 0.396): similar_meaning
- dismal / miserable (PPMI-SVD 0.496, SGNS 0.398): similar_to, synonym
- yes / go (PPMI-SVD 0.516, SGNS 0.417): affirmative response
- trauma / pulmonary (PPMI-SVD 0.685, SGNS 0.531): pulmonary trauma (lung injury)

### near in both: phonetic (2)

- hear / sure (PPMI-SVD 0.651, SGNS 0.417): rhyme
- sorry / silly (PPMI-SVD 0.48, SGNS 0.454): rhyme

### near in both: sequence (1)

- fetal / puberty (PPMI-SVD 0.583, SGNS 0.578): developmental stages

## random, no relation

| relation | pairs | share |
|---|---|---|
| none | 1790 | 89.5% [88.0, 90.9] |
| encyclopedic | 82 | 4.1% [3.2, 5.0] |
| co-hyponym | 36 | 1.8% [1.2, 2.4] |
| orthographic | 28 | 1.4% [0.9, 1.9] |
| same part of speech | 22 | 1.1% [0.7, 1.6] |
| domain | 18 | 0.9% [0.5, 1.3] |
| compound | 16 | 0.8% [0.4, 1.2] |
| function | 10 | 0.5% [0.2, 0.9] |
| synonym | 10 | 0.5% [0.2, 0.8] |
| collocation | 9 | 0.4% [0.2, 0.8] |
| hypernym | 9 | 0.4% [0.2, 0.8] |
| derivation | 7 | 0.4% [0.1, 0.7] |
| attribute | 6 | 0.3% [0.1, 0.5] |
| meronym | 6 | 0.3% [0.1, 0.5] |
| association | 5 | 0.2% [0.1, 0.5] |
| antonym | 3 | 0.1% [0.0, 0.4] |
| cause | 2 | 0.1% [0.0, 0.2] |
| abbreviation | 1 | 0.1% [0.0, 0.1] |
| inflection | 1 | 0.1% [0.0, 0.1] |
| metaphor | 1 | 0.1% [0.0, 0.1] |
| phonetic | 1 | 0.1% [0.0, 0.1] |
| sequence | 1 | 0.1% [0.0, 0.1] |
| translation | 1 | 0.1% [0.0, 0.1] |

### random, no relation: none (1790), first 40

- cultured / armistice (PPMI-SVD 0.117, SGNS 0.059)
- overt / excuse (PPMI-SVD 0.304, SGNS 0.343)
- nicotine / darkened (PPMI-SVD 0.176, SGNS 0.07)
- haifa / scarcely (PPMI-SVD 0.233, SGNS 0.269)
- chaplin / luxury (PPMI-SVD 0.021, SGNS 0.203)
- emu / ariadne (PPMI-SVD 0.081, SGNS 0.023)
- reaching / cajun (PPMI-SVD 0.051, SGNS 0.02)
- bad / accordingly (PPMI-SVD 0.29, SGNS 0.205)
- duo / secularism (PPMI-SVD -0.005, SGNS 0.046)
- avian / midrash (PPMI-SVD 0.046, SGNS 0.065)
- sometime / faroese (PPMI-SVD 0.169, SGNS 0.069)
- privilege / engels (PPMI-SVD 0.276, SGNS 0.202)
- mauritius / journalistic (PPMI-SVD 0.034, SGNS 0.106)
- disney / kantian (PPMI-SVD -0.015, SGNS 0.02)
- fully / focus (PPMI-SVD 0.224, SGNS 0.145)
- fatality / crest (PPMI-SVD 0.07, SGNS 0.001)
- pressure / ideology (PPMI-SVD 0.115, SGNS 0.198)
- draco / promptly (PPMI-SVD 0.217, SGNS 0.271)
- extraordinary / cruel (PPMI-SVD 0.362, SGNS 0.328)
- realist / heterogeneous (PPMI-SVD 0.226, SGNS 0.094)
- consolidated / kidnapping (PPMI-SVD 0.117, SGNS 0.184)
- registered / batch (PPMI-SVD 0.152, SGNS 0.143)
- benin / transformed (PPMI-SVD 0.06, SGNS 0.062)
- fitzgerald / subjectivity (PPMI-SVD 0.04, SGNS 0.134)
- overt / here (PPMI-SVD -0.012, SGNS 0.055)
- combo / marvel (PPMI-SVD 0.025, SGNS 0.21)
- ladder / webster (PPMI-SVD 0.081, SGNS 0.182)
- eritrean / obsession (PPMI-SVD -0.032, SGNS 0.065)
- aroused / burr (PPMI-SVD 0.137, SGNS 0.161)
- derived / fatty (PPMI-SVD 0.326, SGNS 0.166)
- outer / guarantee (PPMI-SVD 0.035, SGNS 0.183)
- proverbs / london (PPMI-SVD -0.039, SGNS 0.054)
- radically / pennsylvania (PPMI-SVD 0.05, SGNS 0.039)
- mirror / smaller (PPMI-SVD 0.149, SGNS 0.091)
- legislation / einstein (PPMI-SVD 0.112, SGNS 0.138)
- binary / pretend (PPMI-SVD -0.056, SGNS 0.084)
- realization / keyboardist (PPMI-SVD 0.07, SGNS 0.053)
- buffer / montezuma (PPMI-SVD 0.029, SGNS 0.022)
- fast / simultaneous (PPMI-SVD 0.41, SGNS 0.323)
- resist / ultimate (PPMI-SVD 0.308, SGNS 0.227)

### random, no relation: encyclopedic (82)

- disaster / hostage (PPMI-SVD 0.276, SGNS 0.362): related_to
- fate / visionary (PPMI-SVD 0.198, SGNS 0.162): both_relate_to_future
- grocery / allergy (PPMI-SVD 0.152, SGNS 0.276): food_allergy_labeling
- augmentation / highlight (PPMI-SVD 0.237, SGNS 0.177): related_concept
- video / size (PPMI-SVD 0.132, SGNS 0.125): attribute
- stream / drainage (PPMI-SVD 0.445, SGNS 0.41): related_to
- hopkins / disambiguation (PPMI-SVD 0.024, SGNS 0.113): related_to
- telecom / geneva (PPMI-SVD 0.105, SGNS 0.246): itu headquarters in geneva
- sting / hive (PPMI-SVD 0.312, SGNS 0.215): associated_with_bees, related_to
- speaker / ruling (PPMI-SVD 0.343, SGNS 0.32): related_to
- worthy / clay (PPMI-SVD 0.047, SGNS 0.083): feet of clay (unworthy despite seeming worthy)
- grandmaster / secretary (PPMI-SVD 0.094, SGNS 0.139): title_of_office
- dodo / whitehall (PPMI-SVD 0.092, SGNS 0.205): both are proper nouns associated with britain (dodo extinct bird of mauritius, former british colony; whitehall british government)
- sea / roach (PPMI-SVD 0.077, SGNS 0.234): habitat
- nightclub / petersburg (PPMI-SVD 0.322, SGNS 0.145): located_in
- expeditionary / franklin (PPMI-SVD -0.009, SGNS 0.056): topical association
- keeper / theft (PPMI-SVD 0.153, SGNS 0.073): related_to
- text / tale (PPMI-SVD 0.277, SGNS 0.382): related_to
- suffrage / democratization (PPMI-SVD 0.246, SGNS 0.344): causes, related_to
- whitehall / lexington (PPMI-SVD 0.457, SGNS 0.415): place_name, street_name
- potential / optional (PPMI-SVD 0.013, SGNS 0.12): related_to
- prelate / tudor (PPMI-SVD 0.357, SGNS 0.186): historical association (tudor-era prelates such as cardinal wolsey)
- mark / herbert (PPMI-SVD 0.237, SGNS 0.265): surnames
- address / burger (PPMI-SVD -0.069, SGNS 0.135): gettysburg address / burger (warren burger, chief justice)
- canon / violation (PPMI-SVD 0.17, SGNS 0.21): canon_violation
- asthma / pollen (PPMI-SVD -0.022, SGNS 0.155): allergen, cause
- experimentally / attempted (PPMI-SVD 0.058, SGNS 0.111): related_concept
- diophantus / greco (PPMI-SVD 0.226, SGNS 0.199): related_to
- garbage / profane (PPMI-SVD 0.132, SGNS 0.097): related_to
- sequencer / guanine (PPMI-SVD 0.065, SGNS 0.221): topical association
- mammal / tundra (PPMI-SVD 0.217, SGNS 0.347): habitat, lives_in
- episcopate / nobility (PPMI-SVD 0.285, SGNS 0.322): overlap via prince-bishops
- persuade / emphasised (PPMI-SVD 0.161, SGNS 0.172): related_to
- appleton / melanchthon (PPMI-SVD 0.056, SGNS 0.114): proper nouns, surnames
- aggregate / count (PPMI-SVD 0.161, SGNS 0.056): related_to
- muscovy / expansionism (PPMI-SVD 0.44, SGNS 0.382): related_to
- prevailing / denver (PPMI-SVD 0.138, SGNS 0.113): colorado
- gunner / watch (PPMI-SVD 0.085, SGNS 0.198): lookout
- foreigner / istanbul (PPMI-SVD 0.139, SGNS 0.114): foreigner visits istanbul
- creature / genetic (PPMI-SVD 0.081, SGNS 0.193): related_to
- popular / sway (PPMI-SVD 0.001, SGNS 0.108): related_to
- procession / conqueror (PPMI-SVD 0.169, SGNS 0.124): related_to
- windows / paul (PPMI-SVD 0.033, SGNS 0.074): paul allen co-founded microsoft (windows)
- devices / debugger (PPMI-SVD 0.074, SGNS 0.436): related_to
- hindi / buddha (PPMI-SVD 0.24, SGNS 0.326): associated_with_india
- terrorism / agency (PPMI-SVD 0.468, SGNS 0.461): counter-terrorism agency
- pension / cio (PPMI-SVD 0.229, SGNS 0.103): cio_labor_union_pension_plans, pension_fund_chief_investment_officer
- embryology / department (PPMI-SVD 0.233, SGNS 0.196): academic_field_and_unit
- havoc / canine (PPMI-SVD 0.076, SGNS -0.04): cry_havoc_dogs_of_war_quotation
- jericho / hartford (PPMI-SVD 0.164, SGNS 0.239): biblical_place_name_and_us_city
- barrier / jump (PPMI-SVD 0.283, SGNS 0.253): related_to
- chest / manly (PPMI-SVD 0.074, SGNS 0.165): association
- head / monarchist (PPMI-SVD 0.11, SGNS 0.117): head of state
- guinea / cartier (PPMI-SVD 0.193, SGNS 0.256): jacques_cartier_and_guinea_both_linked_to_french_exploration
- translation / eusebius (PPMI-SVD 0.393, SGNS 0.306): bible translation
- blast / disabling (PPMI-SVD 0.346, SGNS 0.385): related_to
- advert / geographic (PPMI-SVD 0.047, SGNS -0.042): national_geographic_advertisement
- rockies / yellow (PPMI-SVD 0.053, SGNS 0.185): related_to
- lexical / vector (PPMI-SVD 0.001, SGNS 0.224): related_to
- polynesian / discovery (PPMI-SVD 0.13, SGNS 0.293): related_to
- blade / plow (PPMI-SVD 0.294, SGNS 0.317): related_to
- guatemalan / seaport (PPMI-SVD 0.177, SGNS 0.231): related_to
- horned / ass (PPMI-SVD 0.37, SGNS 0.418): both_animal_related
- reid / boone (PPMI-SVD 0.287, SGNS 0.151): surnames
- bligh / jamaican (PPMI-SVD 0.235, SGNS 0.095): historical association (captain bligh brought breadfruit to jamaica)
- forthcoming / introduce (PPMI-SVD 0.247, SGNS 0.199): related_to
- spy / apache (PPMI-SVD 0.09, SGNS 0.146): military aircraft naming (helicopter types)
- nebula / catalog (PPMI-SVD 0.248, SGNS 0.249): astronomical catalog entry (e.g., messier, ngc)
- discipline / tribulation (PPMI-SVD 0.021, SGNS 0.188): related_to
- binder / tome (PPMI-SVD 0.222, SGNS 0.163): related_to
- activism / marxism (PPMI-SVD 0.47, SGNS 0.394): political_ideology_association, related_to
- reggae / colonialism (PPMI-SVD 0.072, SGNS 0.121): related_to
- prominent / action (PPMI-SVD 0.126, SGNS 0.116): both relate to visibility or impact
- cheek / candida (PPMI-SVD 0.001, SGNS 0.072): body part and microorganism, candida can infect the inner cheek (oral thrush)
- medieval / faith (PPMI-SVD 0.113, SGNS 0.168): topical association
- milwaukee / riga (PPMI-SVD 0.179, SGNS 0.188): milwaukee and riga are sister cities
- gift / seer (PPMI-SVD 0.313, SGNS 0.196): related_to
- ordnance / phosphorus (PPMI-SVD 0.129, SGNS 0.185): related_to
- bulge / range (PPMI-SVD 0.11, SGNS 0.323): battle of the bulge / mountain range (military-geographic terms)
- syria / french (PPMI-SVD 0.076, SGNS 0.178): french_spoken_in_syria, historical_french_mandate
- ale / lunch (PPMI-SVD 0.176, SGNS 0.145): related_to
- magellan / spaniard (PPMI-SVD 0.561, SGNS 0.466): associated_with

### random, no relation: co-hyponym (36)

- soldier / fortress (PPMI-SVD 0.402, SGNS 0.386): both military-related
- organizational / analytical (PPMI-SVD 0.394, SGNS 0.39): both adjectives, co-hyponyms (types of skills)
- push / widen (PPMI-SVD 0.328, SGNS 0.316): both verbs
- periodic / relational (PPMI-SVD 0.101, SGNS 0.178): both adjectives
- sussex / nassau (PPMI-SVD 0.404, SGNS 0.452): both_counties, both_place_names, both_royal_houses_or_dynasties
- encouraging / trustworthy (PPMI-SVD 0.061, SGNS 0.152): both_describe_character, both_positive_adjectives
- mccormick / russell (PPMI-SVD 0.315, SGNS 0.424): both are given names/surnames of notable people, both are scottish/irish surnames, both are surnames
- piedmont / volcanic (PPMI-SVD 0.195, SGNS 0.285): both describe terrain types, geological landforms
- totalitarianism / functionalism (PPMI-SVD 0.391, SGNS 0.477): both_isms, both_political_or_social_theories
- graham / beethoven (PPMI-SVD 0.075, SGNS 0.132): both_surnames
- bonn / scandinavia (PPMI-SVD 0.242, SGNS 0.212): both_in_europe
- disarray / disillusionment (PPMI-SVD 0.424, SGNS 0.233): both negative states
- mark / herbert (PPMI-SVD 0.237, SGNS 0.265): male given names
- georgetown / montreal (PPMI-SVD 0.247, SGNS 0.286): both_cities, co_hyponyms
- gig / musical (PPMI-SVD 0.318, SGNS 0.431): events in music
- episcopate / nobility (PPMI-SVD 0.285, SGNS 0.322): both are ruling elites, co-hyponyms (social estates/classes)
- servo / ram (PPMI-SVD 0.219, SGNS 0.254): both are actuator/hydraulic components (servo-ram)
- poetical / considerable (PPMI-SVD 0.293, SGNS 0.272): both adjectives
- aggregate / count (PPMI-SVD 0.161, SGNS 0.056): aggregate_function
- jury / caravan (PPMI-SVD 0.055, SGNS 0.045): collective_nouns, group_of_people
- galician / aboriginal (PPMI-SVD 0.464, SGNS 0.402): both demonyms/ethnic adjectives, both refer to peoples or languages
- jericho / hartford (PPMI-SVD 0.164, SGNS 0.239): us_place_names
- heavily / badly (PPMI-SVD 0.297, SGNS 0.3): degree adverb
- engraved / handled (PPMI-SVD 0.007, SGNS 0.121): both adjectives
- compress / circumvent (PPMI-SVD 0.291, SGNS 0.129): both verbs
- lookout / shipowner (PPMI-SVD 0.075, SGNS 0.267): maritime_occupations, ship_crew_and_owner
- justinian / lysander (PPMI-SVD 0.025, SGNS 0.161): both ancient rulers or commanders, both historical figures
- vie / timbre (PPMI-SVD -0.042, SGNS 0.041): both_french_words
- reid / boone (PPMI-SVD 0.287, SGNS 0.151): us_tv_actors
- binder / tome (PPMI-SVD 0.222, SGNS 0.163): book_like_object
- jerusalem / cologne (PPMI-SVD 0.281, SGNS 0.378): both cities, both have famous cathedrals or holy sites, both pilgrimage destinations
- hammett / bethe (PPMI-SVD 0.137, SGNS 0.193): both_surnames_of_famous_people
- milwaukee / riga (PPMI-SVD 0.179, SGNS 0.188): both cities, both port cities
- bulge / range (PPMI-SVD 0.11, SGNS 0.323): both verbs
- peel / scramble (PPMI-SVD 0.138, SGNS 0.132): food preparation verbs, things done to eggs
- gibbs / gillespie (PPMI-SVD 0.204, SGNS 0.254): both family names of scottish origin, both surnames

### random, no relation: orthographic (28)

- observance / hands (PPMI-SVD 0.074, SGNS 0.17): both contain the letter a, both contain the letter e, both contain the letter n, both contain the letter s
- longevity / apartheid (PPMI-SVD 0.076, SGNS 0.126): both contain the letter e, both contain the letter i, both contain the letter t
- crying / antigen (PPMI-SVD -0.005, SGNS -0.032): both contain the letter g, both contain the letter i, both contain the letter n
- organizational / analytical (PPMI-SVD 0.394, SGNS 0.39): both end in -al
- osiris / sos (PPMI-SVD 0.171, SGNS 0.104): subanagram
- judgment / remembrance (PPMI-SVD 0.207, SGNS 0.295): both_end_in_suffix
- dissident / discriminate (PPMI-SVD 0.072, SGNS 0.11): shared_letters
- procurement / polemical (PPMI-SVD 0.078, SGNS 0.067): same first letter
- ire / off (PPMI-SVD 0.015, SGNS 0.051): anagram-adjacent letters
- carson / carbohydrate (PPMI-SVD 0.022, SGNS 0.119): same_initial_letters
- ton / nina (PPMI-SVD 0.122, SGNS 0.067): anagram-like letter overlap (n), nina contains 'n' as ton ends with 'n'
- financial / n (PPMI-SVD 0.028, SGNS 0.051): contains letter n
- tragic / training (PPMI-SVD 0.025, SGNS 0.129): orthographic_prefix_overlap, same_initial_letters_tra
- cli / cost (PPMI-SVD 0.115, SGNS 0.333): same_initial_letter
- prevailing / denver (PPMI-SVD 0.138, SGNS 0.113): contains_colorado_place_vail
- annihilated / keyed (PPMI-SVD 0.051, SGNS 0.085): both verb forms ending in -ed
- hobby / ee (PPMI-SVD -0.006, SGNS 0.047): both contain a doubled letter
- childless / cemetery (PPMI-SVD 0.086, SGNS 0.234): same_first_letter
- crucifixion / encapsulation (PPMI-SVD -0.01, SGNS 0.099): both end in -ion
- padded / faster (PPMI-SVD 0.143, SGNS 0.241): same_length
- viper / gear (PPMI-SVD 0.302, SGNS 0.353): anagram_minus_letter
- vigorously / improperly (PPMI-SVD 0.155, SGNS 0.374): both end in -ly
- brussels / cs (PPMI-SVD 0.063, SGNS 0.115): shared letter
- supposition / suspension (PPMI-SVD -0.01, SGNS 0.049): both nouns ending in -tion/-sion
- illegal / augment (PPMI-SVD 0.169, SGNS 0.215): same_length
- hammett / bethe (PPMI-SVD 0.137, SGNS 0.193): both_contain_letters_h_e_t
- away / avian (PPMI-SVD -0.05, SGNS 0.035): shared_first_letter
- entirely / spire (PPMI-SVD 0.195, SGNS 0.254): anagram

### random, no relation: same part of speech (22)

- beheading / walking (PPMI-SVD 0.128, SGNS 0.265): both_gerunds
- riding / listed (PPMI-SVD 0.1, SGNS 0.125): both_verb_forms
- longevity / apartheid (PPMI-SVD 0.076, SGNS 0.126): both are nouns
- judgment / remembrance (PPMI-SVD 0.207, SGNS 0.295): both_abstract_nouns
- ambient / stereotypical (PPMI-SVD 0.028, SGNS 0.092): both are adjectives
- disarray / disillusionment (PPMI-SVD 0.424, SGNS 0.233): both nouns
- credence / justice (PPMI-SVD -0.02, SGNS 0.065): abstract nouns
- felt / saturated (PPMI-SVD -0.005, SGNS -0.009): both past participles
- tragic / training (PPMI-SVD 0.025, SGNS 0.129): both_adjectives_or_nouns_no
- prescribe / effected (PPMI-SVD 0.258, SGNS 0.029): both_verbs
- annihilated / keyed (PPMI-SVD 0.051, SGNS 0.085): both past participles
- looking / tempting (PPMI-SVD 0.341, SGNS 0.273): both_present_participles
- expel / undertake (PPMI-SVD 0.399, SGNS 0.305): both_verbs
- crucifixion / encapsulation (PPMI-SVD -0.01, SGNS 0.099): both nouns
- subscriber / calculation (PPMI-SVD 0.025, SGNS 0.238): both nouns
- damage / advise (PPMI-SVD -0.019, SGNS 0.111): both_nouns_and_verbs_partially, both_verbs
- engraved / handled (PPMI-SVD 0.007, SGNS 0.121): both past participles
- extra / instant (PPMI-SVD 0.133, SGNS 0.226): both_adjectives, both_nouns
- motivated / identified (PPMI-SVD 0.193, SGNS 0.265): both -ed adjectives, both past participles
- vigorously / improperly (PPMI-SVD 0.155, SGNS 0.374): both adverbs
- task / box (PPMI-SVD 0.129, SGNS 0.114): both_noun_and_verb
- bulge / range (PPMI-SVD 0.11, SGNS 0.323): both nouns

### random, no relation: domain (18)

- disaster / hostage (PPMI-SVD 0.276, SGNS 0.362): crisis_context
- shear / tennis (PPMI-SVD -0.015, SGNS 0.14): physics of a tennis ball's spin (shear forces)
- monasticism / yeshiva (PPMI-SVD 0.037, SGNS 0.326): religious_education, religious_institution
- bounds / core (PPMI-SVD 0.101, SGNS 0.205): array bounds vs core memory (computing)
- grandmaster / secretary (PPMI-SVD 0.094, SGNS 0.139): chess_term
- text / tale (PPMI-SVD 0.277, SGNS 0.382): narrative, story
- gig / musical (PPMI-SVD 0.318, SGNS 0.431): musical performance, topically related
- credence / justice (PPMI-SVD -0.02, SGNS 0.065): legal concepts
- confess / gendarmerie (PPMI-SVD -0.043, SGNS 0.058): topical association (police interrogation/confession)
- macabre / abuse (PPMI-SVD 0.051, SGNS 0.184): topical_association
- gunner / watch (PPMI-SVD 0.085, SGNS 0.198): military_duty
- listener / chain (PPMI-SVD 0.013, SGNS 0.184): computing domain, listener chain (computing)
- prophetic / mojo (PPMI-SVD 0.067, SGNS 0.164): supernatural_association
- injection / pediatric (PPMI-SVD 0.258, SGNS 0.241): medical_domain
- pronoun / script (PPMI-SVD 0.229, SGNS 0.276): topical_association
- riding / hurdles (PPMI-SVD 0.177, SGNS 0.176): show_jumping_obstacle
- advert / geographic (PPMI-SVD 0.047, SGNS -0.042): magazine_context
- overflow / std (PPMI-SVD 0.393, SGNS 0.387): c++_terms, programming_terms

### random, no relation: compound (16)

- lady / veil (PPMI-SVD 0.251, SGNS 0.27): bridal_veil
- completely / void (PPMI-SVD 0.291, SGNS 0.246): collocation
- reading / out (PPMI-SVD 0.102, SGNS 0.235): compound
- food / locator (PPMI-SVD 0.076, SGNS 0.246): compound (food locator)
- magazine / retracted (PPMI-SVD 0.209, SGNS 0.278): collocation
- two / pass (PPMI-SVD -0.001, SGNS 0.127): collocation
- servo / ram (PPMI-SVD 0.219, SGNS 0.254): compound: servo ram
- speaker / salon (PPMI-SVD 0.073, SGNS 0.067): co-occurrence
- sympathetic / circumstances (PPMI-SVD 0.265, SGNS 0.207): collocation
- interpret / musically (PPMI-SVD 0.095, SGNS 0.111): collocation
- decorate / hair (PPMI-SVD 0.173, SGNS 0.325): collocation
- terrorism / agency (PPMI-SVD 0.468, SGNS 0.461): co-occurrence
- fund / inaugural (PPMI-SVD 0.044, SGNS 0.136): collocation
- injection / pediatric (PPMI-SVD 0.258, SGNS 0.241): collocation
- healthcare / mismanagement (PPMI-SVD 0.245, SGNS 0.288): collocation
- insanity / bunker (PPMI-SVD 0.024, SGNS 0.067): bunker mentality

### random, no relation: function (10)

- lady / veil (PPMI-SVD 0.251, SGNS 0.27): wears
- soldier / fortress (PPMI-SVD 0.402, SGNS 0.386): soldiers garrison a fortress
- freelance / midwifery (PPMI-SVD 0.24, SGNS 0.158): work_mode_of_practitioner
- rotation / carbide (PPMI-SVD -0.035, SGNS 0.109): carbide tools used in rotary cutting
- automobile / insured (PPMI-SVD 0.141, SGNS 0.187): insured object
- devices / debugger (PPMI-SVD 0.074, SGNS 0.436): debugger is a tool used on devices
- bring / dominos (PPMI-SVD 0.183, SGNS 0.234): domino's_brings_delivered_pizza
- barrier / jump (PPMI-SVD 0.283, SGNS 0.253): obstacle_for
- ceremony / poetry (PPMI-SVD 0.072, SGNS 0.217): poetry is recited at ceremonies
- binder / tome (PPMI-SVD 0.222, SGNS 0.163): holds_pages

### random, no relation: synonym (10)

- push / widen (PPMI-SVD 0.328, SGNS 0.316): both can mean expanding outward
- hairy / intractable (PPMI-SVD 0.169, SGNS 0.223): synonym (informal: difficult)
- ire / off (PPMI-SVD 0.015, SGNS 0.051): ticked off
- derivation / reckoning (PPMI-SVD 0.227, SGNS 0.224): synonym
- convergence / coordinated (PPMI-SVD 0.213, SGNS 0.145): semantic similarity
- factoring / extract (PPMI-SVD 0.17, SGNS 0.211): both mean pulling out a component, synonyms in mathematics (factoring out / extracting a factor)
- sickly / rebound (PPMI-SVD 0.143, SGNS 0.14): rebound as recovery from sickness
- preserved / prolonged (PPMI-SVD 0.05, SGNS 0.019): similar meaning
- heavily / badly (PPMI-SVD 0.297, SGNS 0.3): synonym
- overriding / meaningful (PPMI-SVD 0.288, SGNS 0.265): both describe importance, near-synonyms in the sense of significant

### random, no relation: collocation (9)

- reading / out (PPMI-SVD 0.102, SGNS 0.235): phrasal_verb
- sting / hive (PPMI-SVD 0.312, SGNS 0.215): co_occurrence
- bounds / core (PPMI-SVD 0.101, SGNS 0.205): out of bounds
- safety / signal (PPMI-SVD 0.144, SGNS 0.2): collocation (safety signal)
- procession / conqueror (PPMI-SVD 0.169, SGNS 0.124): triumphal procession
- heavily / badly (PPMI-SVD 0.297, SGNS 0.3): intensifier
- loss / put (PPMI-SVD 0.186, SGNS 0.178): phrase_put_at_a_loss
- shifting / fortune (PPMI-SVD 0.074, SGNS 0.042): collocation (shifting fortunes)
- prominent / action (PPMI-SVD 0.126, SGNS 0.116): prominent action (collocation)

### random, no relation: hypernym (9)

- place / hampshire (PPMI-SVD 0.16, SGNS 0.183): hypernym, instance of
- regina / supreme (PPMI-SVD 0.122, SGNS 0.238): queen as supreme ruler
- wyoming / area (PPMI-SVD 0.257, SGNS 0.426): isa
- rickey / mixture (PPMI-SVD 0.142, SGNS 0.196): hypernym, is_a
- aggregate / count (PPMI-SVD 0.161, SGNS 0.056): hypernym
- racing / crab (PPMI-SVD 0.137, SGNS 0.32): crab racing (a type of race)
- chamberlain / executive (PPMI-SVD 0.205, SGNS 0.251): hypernym
- benefit / stroke (PPMI-SVD 0.135, SGNS 0.159): stroke of luck is a benefit
- riding / hurdles (PPMI-SVD 0.177, SGNS 0.176): athletics_event, equestrian_sport_event

### random, no relation: derivation (7)

- disarray / disillusionment (PPMI-SVD 0.424, SGNS 0.233): shared prefix dis-
- emergency / emulate (PPMI-SVD 0.009, SGNS 0.042): shared prefix em-
- deliverance / reliance (PPMI-SVD 0.118, SGNS 0.114): shared suffix -ance
- positivist / maintainer (PPMI-SVD 0.063, SGNS 0.109): agent_noun_suffix_pattern
- heavily / badly (PPMI-SVD 0.297, SGNS 0.3): adverb
- supposition / suspension (PPMI-SVD -0.01, SGNS 0.049): shared prefix sup-/sus-
- renunciation / reconstruct (PPMI-SVD 0.009, SGNS -0.003): shared prefix re-

### random, no relation: attribute (6)

- lineman / endurance (PPMI-SVD -0.021, SGNS 0.214): endurance is a trait required of a lineman
- length / truss (PPMI-SVD 0.483, SGNS 0.409): a truss has length as a structural dimension
- rusty / coyote (PPMI-SVD 0.437, SGNS 0.281): color_of_fur
- felt / saturated (PPMI-SVD -0.005, SGNS -0.009): felt can be saturated
- wyoming / area (PPMI-SVD 0.257, SGNS 0.426): hasproperty
- bodhisattva / intermediate (PPMI-SVD 0.085, SGNS 0.114): hasproperty

### random, no relation: meronym (6)

- crying / antigen (PPMI-SVD -0.005, SGNS -0.032): tears contain antibodies that bind antigens
- stream / drainage (PPMI-SVD 0.445, SGNS 0.41): part_of
- suffrage / democratization (PPMI-SVD 0.246, SGNS 0.344): part_of
- windows / paul (PPMI-SVD 0.033, SGNS 0.074): st paul's cathedral windows
- blade / plow (PPMI-SVD 0.294, SGNS 0.317): part_of
- cottage / floor (PPMI-SVD 0.253, SGNS 0.29): has_part, part_of

### random, no relation: association (5)

- burn / indignation (PPMI-SVD 0.086, SGNS 0.126): related_emotion
- regina / supreme (PPMI-SVD 0.122, SGNS 0.238): semantic association
- sexy / mate (PPMI-SVD 0.027, SGNS 0.016): semantic association
- technology / hubris (PPMI-SVD 0.017, SGNS -0.006): thematic_association
- supposition / suspension (PPMI-SVD -0.01, SGNS 0.049): suspension of disbelief relates to supposition

### random, no relation: antonym (3)

- sickly / rebound (PPMI-SVD 0.143, SGNS 0.14): antonym-like (sickly vs recovering/rebounding)
- avoid / instigation (PPMI-SVD -0.032, SGNS 0.072): antonym_of
- civilian / mil (PPMI-SVD 0.194, SGNS 0.35): antonym, contrast

### random, no relation: cause (2)

- push / widen (PPMI-SVD 0.328, SGNS 0.316): push can cause widening
- asthma / pollen (PPMI-SVD -0.022, SGNS 0.155): trigger

### random, no relation: abbreviation (1)

- tanakh / darpa (PPMI-SVD 0.011, SGNS 0.031): both acronyms

### random, no relation: inflection (1)

- preserved / prolonged (PPMI-SVD 0.05, SGNS 0.019): past participle

### random, no relation: metaphor (1)

- burn / indignation (PPMI-SVD 0.086, SGNS 0.126): metaphor

### random, no relation: phonetic (1)

- deliverance / reliance (PPMI-SVD 0.118, SGNS 0.114): rhyme

### random, no relation: sequence (1)

- feast / dismantled (PPMI-SVD 0.034, SGNS -0.013): a feast setup gets dismantled after the meal

### random, no relation: translation (1)

- regina / supreme (PPMI-SVD 0.122, SGNS 0.238): regina means queen

## random, any

| relation | pairs | share |
|---|---|---|
| none | 897 | 89.7% [87.8, 91.5] |
| encyclopedic | 34 | 3.4% [2.3, 4.6] |
| co-hyponym | 19 | 1.9% [1.1, 2.8] |
| same part of speech | 16 | 1.6% [0.9, 2.4] |
| orthographic | 12 | 1.2% [0.6, 1.9] |
| domain | 8 | 0.8% [0.3, 1.3] |
| compound | 7 | 0.7% [0.2, 1.3] |
| synonym | 7 | 0.7% [0.2, 1.2] |
| association | 5 | 0.5% [0.1, 0.9] |
| derivation | 5 | 0.5% [0.1, 1.0] |
| antonym | 4 | 0.4% [0.1, 0.8] |
| attribute | 3 | 0.3% [0.0, 0.7] |
| hypernym | 3 | 0.3% [0.0, 0.7] |
| meronym | 3 | 0.3% [0.0, 0.6] |
| phonetic | 3 | 0.3% [0.0, 0.7] |
| function | 2 | 0.2% [0.0, 0.5] |
| inflection | 2 | 0.2% [0.0, 0.5] |
| collocation | 1 | 0.1% [0.0, 0.4] |
| offspring | 1 | 0.1% [0.0, 0.3] |
| scale | 1 | 0.1% [0.0, 0.3] |
| sequence | 1 | 0.1% [0.0, 0.3] |

### random, any: none (897), first 40

- collective / convenience (PPMI-SVD 0.201, SGNS 0.258)
- roth / bringing (PPMI-SVD 0.11, SGNS 0.144)
- rally / cable (PPMI-SVD -0.001, SGNS 0.188)
- basil / shanghai (PPMI-SVD 0.14, SGNS 0.158)
- absolute / filmmaker (PPMI-SVD 0.054, SGNS 0.021)
- primacy / eight (PPMI-SVD 0.001, SGNS 0.051)
- mayoral / convert (PPMI-SVD -0.076, SGNS -0.096)
- allied / unfavourable (PPMI-SVD 0.193, SGNS 0.205)
- westernmost / reconstruct (PPMI-SVD 0.072, SGNS 0.22)
- thyroid / mag (PPMI-SVD 0.071, SGNS 0.221)
- collagen / ives (PPMI-SVD 0.014, SGNS 0.046)
- planck / thyroid (PPMI-SVD -0.032, SGNS 0.13)
- oriole / each (PPMI-SVD 0.064, SGNS 0.179)
- rehabilitation / visit (PPMI-SVD 0.197, SGNS 0.235)
- staunchly / dos (PPMI-SVD -0.074, SGNS -0.047)
- switch / noted (PPMI-SVD 0.058, SGNS 0.101)
- intangible / harpoon (PPMI-SVD 0.048, SGNS -0.042)
- monomer / strategy (PPMI-SVD -0.097, SGNS 0.094)
- skeleton / statement (PPMI-SVD 0.033, SGNS 0.156)
- swaziland / superintendent (PPMI-SVD 0.103, SGNS 0.048)
- tentative / manichaeism (PPMI-SVD 0.151, SGNS 0.147)
- subsurface / distinctively (PPMI-SVD 0.124, SGNS 0.027)
- amusing / adult (PPMI-SVD 0.159, SGNS 0.066)
- father / aa (PPMI-SVD -0.006, SGNS -0.022)
- translate / interrupt (PPMI-SVD 0.209, SGNS 0.226)
- scripted / geographical (PPMI-SVD 0.048, SGNS 0.041)
- aegis / android (PPMI-SVD 0.137, SGNS 0.13)
- precaution / misogyny (PPMI-SVD 0.32, SGNS 0.105)
- marrakesh / symbolic (PPMI-SVD 0.011, SGNS 0.135)
- billiards / herbaceous (PPMI-SVD 0.091, SGNS 0.08)
- geology / indivisible (PPMI-SVD -0.039, SGNS 0.161)
- astrobiology / saxe (PPMI-SVD 0.027, SGNS -0.013)
- el / madagascar (PPMI-SVD 0.032, SGNS 0.245)
- passion / aspirin (PPMI-SVD 0.055, SGNS 0.051)
- scale / factorization (PPMI-SVD 0.078, SGNS 0.287)
- himmler / neuron (PPMI-SVD 0.015, SGNS 0.022)
- seeker / fijian (PPMI-SVD 0.05, SGNS 0.056)
- appellation / faulty (PPMI-SVD 0.215, SGNS 0.104)
- stylistic / benchmark (PPMI-SVD 0.286, SGNS 0.255)
- toll / predominant (PPMI-SVD -0.008, SGNS 0.101)

### random, any: encyclopedic (34)

- colorful / cartoonist (PPMI-SVD 0.114, SGNS 0.215): related_to
- hook / huygens (PPMI-SVD 0.102, SGNS 0.077): priority dispute over the balance spring in watches (hooke vs. huygens)
- baseline / sampling (PPMI-SVD 0.335, SGNS 0.347): related_to
- performance / conformity (PPMI-SVD 0.035, SGNS 0.144): related_to
- honeymoon / inclusive (PPMI-SVD 0.178, SGNS -0.028): all-inclusive honeymoon package
- acetylene / uranus (PPMI-SVD 0.027, SGNS 0.168): both found in astronomy contexts (acetylene detected in uranus's atmosphere)
- microscopic / inspection (PPMI-SVD 0.111, SGNS 0.136): topical association
- collision / cartoon (PPMI-SVD 0.02, SGNS 0.146): slapstick cartoon trope
- waldheim / blamed (PPMI-SVD 0.32, SGNS 0.289): related_to
- association / nationalist (PPMI-SVD 0.122, SGNS 0.138): nationalist association
- reporter / actuality (PPMI-SVD 0.051, SGNS 0.063): related_to
- percussion / hands (PPMI-SVD 0.191, SGNS 0.225): percussion instruments are played with the hands
- bush / sideways (PPMI-SVD -0.028, SGNS 0.073): both films (bush-related film 'w.' aside, 'sideways' is a film)
- liquid / refresh (PPMI-SVD 0.021, SGNS 0.237): related_to
- clockwise / nuts (PPMI-SVD 0.012, SGNS 0.042): nuts and bolts: clockwise is the direction you turn a nut to tighten it
- bovine / mutiny (PPMI-SVD 0.019, SGNS 0.045): bounty_mutiny_breadfruit_not_bovine
- pawn / bitmap (PPMI-SVD -0.018, SGNS 0.139): chess piece rendered as bitmap
- robotics / compute (PPMI-SVD 0.178, SGNS 0.235): related_to
- wallace / digest (PPMI-SVD 0.111, SGNS 0.147): founder_of (dewitt wallace founded reader's digest)
- princeton / amazon (PPMI-SVD -0.062, SGNS -0.052): amazon_founder_bezos_princeton_alumnus
- loader / firearm (PPMI-SVD 0.266, SGNS 0.306): related_to
- aura / cancer (PPMI-SVD 0.109, SGNS 0.208): aura as a symptom felt before a migraine or seizure, sometimes linked to brain tumors
- computationally / checksum (PPMI-SVD 0.411, SGNS 0.449): topical association
- fluorescence / intermolecular (PPMI-SVD 0.275, SGNS 0.442): related_to
- sparkling / digestive (PPMI-SVD 0.119, SGNS 0.15): related_to
- stout / detective (PPMI-SVD 0.088, SGNS 0.331): rex_stout_detective_fiction_author
- pump / fps (PPMI-SVD 0.025, SGNS 0.118): pump-action weapons in fps games
- marine / christopher (PPMI-SVD 0.091, SGNS 0.145): saint christopher is patron saint of travelers and mariners
- poisonous / scorpion (PPMI-SVD 0.214, SGNS 0.299): attribute
- sclerosis / neuron (PPMI-SVD 0.652, SGNS 0.542): topical association
- stratum / kerosene (PPMI-SVD 0.142, SGNS 0.099): kerosene derived from petroleum found in rock strata
- navigation / colonisation (PPMI-SVD 0.098, SGNS 0.123): historical_association
- birthday / sad (PPMI-SVD 0.205, SGNS 0.147): associated_with
- legs / graceful (PPMI-SVD 0.462, SGNS 0.505): related_to

### random, any: co-hyponym (19)

- ampere / pauling (PPMI-SVD 0.162, SGNS 0.265): both physicists/chemists with eponymous concepts (ampere unit, pauling electronegativity scale), both surnames of scientists
- percussion / hands (PPMI-SVD 0.191, SGNS 0.225): hand percussion
- boxed / curling (PPMI-SVD 0.114, SGNS 0.247): sports (boxing, curling)
- armstrong / contender (PPMI-SVD 0.177, SGNS 0.148): competitor
- wilkins / wigner (PPMI-SVD 0.475, SGNS 0.313): both nobel laureates, both physicists
- galilee / zephaniah (PPMI-SVD 0.348, SGNS 0.453): biblical_names
- python / nu (PPMI-SVD 0.102, SGNS -0.005): both programming languages
- rand / steinbeck (PPMI-SVD 0.46, SGNS 0.279): both_20th_century_authors, both_american_novelists
- chen / martin (PPMI-SVD 0.007, SGNS 0.302): both surnames
- princeton / amazon (PPMI-SVD -0.062, SGNS -0.052): proper_nouns
- definitely / virtually (PPMI-SVD 0.337, SGNS 0.162): degree/certainty modifiers
- icarus / isaac (PPMI-SVD 0.145, SGNS 0.136): biblical_and_mythological_sons_endangered_by_fathers
- neurological / phonology (PPMI-SVD 0.02, SGNS 0.204): both are fields studied in linguistics/neurolinguistics
- hepatic / linguistic (PPMI-SVD 0.04, SGNS 0.102): both adjectives
- gallop / mills (PPMI-SVD 0.185, SGNS 0.141): both surnames
- dove / jaguar (PPMI-SVD 0.322, SGNS 0.231): both animals, both brand names
- clothed / imprisoned (PPMI-SVD 0.05, SGNS 0.219): both describe a person's state
- paste / brine (PPMI-SVD 0.839, SGNS 0.547): both food preparation media, both mixtures
- sandwich / ring (PPMI-SVD 0.135, SGNS 0.255): both verbs

### random, any: same part of speech (16)

- implicated / annihilated (PPMI-SVD 0.078, SGNS 0.196): both_past_participles
- electrically / sometimes (PPMI-SVD 0.044, SGNS 0.331): same_part_of_speech
- baking / insisting (PPMI-SVD 0.003, SGNS 0.019): both present participles
- geography / qualification (PPMI-SVD -0.045, SGNS 0.132): both nouns
- insult / extract (PPMI-SVD -0.016, SGNS 0.1): both_noun_and_verb
- stricken / fearsome (PPMI-SVD 0.191, SGNS 0.083): both_adjectives
- definitely / virtually (PPMI-SVD 0.337, SGNS 0.162): both adverbs
- disruption / decipherment (PPMI-SVD 0.04, SGNS 0.141): both_deverbal_nouns
- born / preferred (PPMI-SVD 0.032, SGNS 0.178): both past participles
- departed / sewn (PPMI-SVD 0.196, SGNS 0.144): same_part_of_speech
- clothed / imprisoned (PPMI-SVD 0.05, SGNS 0.219): both past participles
- roasted / spelt (PPMI-SVD 0.289, SGNS 0.326): both can be past tense or past participle verb forms
- sandwich / ring (PPMI-SVD 0.135, SGNS 0.255): both nouns
- economically / grammatically (PPMI-SVD 0.147, SGNS 0.187): both adverbs
- playing / compounding (PPMI-SVD -0.136, SGNS -0.054): both_present_participles
- navigation / colonisation (PPMI-SVD 0.098, SGNS 0.123): both_nouns_of_action

### random, any: orthographic (12)

- montage / adversely (PPMI-SVD 0.036, SGNS 0.065): both contain the letter a, both contain the letter e, both contain the letter n, both contain the letter t
- cuttlefish / cannae (PPMI-SVD 0.044, SGNS 0.073): both contain a double letter, same first letter
- adaptive / adopt (PPMI-SVD 0.081, SGNS 0.17): near-homograph
- roe / ji (PPMI-SVD 0.132, SGNS 0.142): anagram_of_reversal
- princeton / amazon (PPMI-SVD -0.062, SGNS -0.052): same_ending_on
- mandelbrot / magnesium (PPMI-SVD 0.038, SGNS 0.196): same_first_two_letters
- disruption / decipherment (PPMI-SVD 0.04, SGNS 0.141): same_first_letter
- barrels / junkers (PPMI-SVD 0.058, SGNS 0.136): anagram
- seat / atop (PPMI-SVD 0.223, SGNS 0.314): anagram
- hepatic / linguistic (PPMI-SVD 0.04, SGNS 0.102): both end in -ic
- anagram / taiwan (PPMI-SVD -0.032, SGNS 0.002): both_contain_repeated_letter_a
- economically / grammatically (PPMI-SVD 0.147, SGNS 0.187): both end in -ically

### random, any: domain (8)

- distance / linearity (PPMI-SVD 0.056, SGNS 0.166): mathematical_concepts
- current / bow (PPMI-SVD -0.061, SGNS 0.011): nautical_terms
- governance / homeostasis (PPMI-SVD 0.183, SGNS 0.236): system control
- armstrong / contender (PPMI-SVD 0.177, SGNS 0.148): boxing
- robotics / compute (PPMI-SVD 0.178, SGNS 0.235): topical_association
- fluorescence / intermolecular (PPMI-SVD 0.275, SGNS 0.442): physical_chemistry_domain
- theme / funk (PPMI-SVD 0.21, SGNS 0.288): music
- kernel / setting (PPMI-SVD 0.093, SGNS 0.084): computing_context

### random, any: compound (7)

- transsexual / ism (PPMI-SVD 0.168, SGNS 0.09): compound_word
- examination / sociological (PPMI-SVD 0.309, SGNS 0.282): collocation
- upscale / fare (PPMI-SVD 0.384, SGNS 0.293): collocation
- cyrus / divide (PPMI-SVD 0.037, SGNS 0.134): combine_with_great
- loader / firearm (PPMI-SVD 0.266, SGNS 0.306): compound_part
- population / packed (PPMI-SVD 0.099, SGNS 0.089): collocation
- disability / stereotypical (PPMI-SVD 0.229, SGNS 0.343): collocation

### random, any: synonym (7)

- contamination / poisoning (PPMI-SVD 0.554, SGNS 0.471): synonym
- up / awakened (PPMI-SVD 0.136, SGNS 0.195): similar_to, synonym
- collective / interconnected (PPMI-SVD 0.09, SGNS 0.191): similar_meaning
- safe / immune (PPMI-SVD 0.12, SGNS 0.291): similar_to, synonym
- revolve / reel (PPMI-SVD 0.133, SGNS 0.144): synonym
- loan / sweetener (PPMI-SVD -0.005, SGNS 0.006): sweetener can mean an extra incentive added to a loan deal
- first / onset (PPMI-SVD 0.063, SGNS 0.202): synonym

### random, any: association (5)

- adaptive / adopt (PPMI-SVD 0.081, SGNS 0.17): semantic association (adapt/adopt confusion)
- gradually / diffusion (PPMI-SVD 0.148, SGNS 0.265): semantic association (diffusion occurs gradually)
- stricken / fearsome (PPMI-SVD 0.191, SGNS 0.083): related_to_fear
- revolve / reel (PPMI-SVD 0.133, SGNS 0.144): rotation, spin
- barge / diving (PPMI-SVD 0.327, SGNS 0.343): water

### random, any: derivation (5)

- implicated / annihilated (PPMI-SVD 0.078, SGNS 0.196): same_suffix_-ated
- transsexual / ism (PPMI-SVD 0.168, SGNS 0.09): suffixation
- adaptive / adopt (PPMI-SVD 0.081, SGNS 0.17): shared prefix ad-
- baking / insisting (PPMI-SVD 0.003, SGNS 0.019): same suffix -ing
- geography / qualification (PPMI-SVD -0.045, SGNS 0.132): shared suffix -tion/-y nouns

### random, any: antonym (4)

- garbage / pure (PPMI-SVD 0.06, SGNS 0.061): antonym
- animate / stop (PPMI-SVD -0.137, SGNS 0.077): antonym
- lot / rarity (PPMI-SVD 0.281, SGNS 0.147): antonym
- birthday / sad (PPMI-SVD 0.205, SGNS 0.147): antonym_connotation

### random, any: attribute (3)

- bush / sideways (PPMI-SVD -0.028, SGNS 0.073): a bush can grow sideways
- poisonous / scorpion (PPMI-SVD 0.214, SGNS 0.299): property_of
- alone / resonant (PPMI-SVD 0.105, SGNS 0.09): a lone voice or note can be resonant

### random, any: hypernym (3)

- contamination / poisoning (PPMI-SVD 0.554, SGNS 0.471): hypernym
- habakkuk / utterance (PPMI-SVD 0.103, SGNS 0.333): habakkuk is a book of prophetic utterance
- marine / christopher (PPMI-SVD 0.091, SGNS 0.145): christopher columbus was a mariner

### random, any: meronym (3)

- word / questionnaire (PPMI-SVD -0.093, SGNS 0.0): meronym, part_of
- plateau / vietnam (PPMI-SVD 0.166, SGNS 0.165): meronymy
- stripes / vane (PPMI-SVD 0.234, SGNS 0.332): flag_features

### random, any: phonetic (3)

- hook / huygens (PPMI-SVD 0.102, SGNS 0.077): 17th-century scientists (robert hooke and christiaan huygens; 'hook' as a near-homophone of hooke)
- oman / brahman (PPMI-SVD -0.026, SGNS 0.042): rhyme
- rear / sheer (PPMI-SVD 0.237, SGNS 0.16): rhyme

### random, any: function (2)

- governance / homeostasis (PPMI-SVD 0.183, SGNS 0.236): regulation
- page / chronicler (PPMI-SVD 0.055, SGNS 0.102): a page holds a chronicle, chronicler writes on pages

### random, any: inflection (2)

- boxed / curling (PPMI-SVD 0.114, SGNS 0.247): past tense/participle forms (boxed, curled)
- departed / sewn (PPMI-SVD 0.196, SGNS 0.144): past_participle_form

### random, any: collocation (1)

- honeymoon / inclusive (PPMI-SVD 0.178, SGNS -0.028): travel collocation

### random, any: offspring (1)

- icarus / isaac (PPMI-SVD 0.145, SGNS 0.136): names_of_sons_in_narratives

### random, any: scale (1)

- priority / third (PPMI-SVD 0.102, SGNS 0.201): ranking

### random, any: sequence (1)

- first / onset (PPMI-SVD 0.063, SGNS 0.202): beginning
