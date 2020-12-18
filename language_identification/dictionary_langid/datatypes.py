from collections import Counter
from dataclasses import dataclass
from dataclasses import field
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

from tokenizer import text_n_grams
from tokenizer import unicode_tokenize


@dataclass
class Dictionary:
    term_language: str
    definition_language: str
    data_source: Optional[str] = field(default=None)

    # vocabulary: word <-> word_index
    vocabulary: List[str] = field(default_factory=list)  # word_index -> word
    _vocab_indices: Dict[str, int] = field(default_factory=dict)  # word -> word_index

    # terms and definitions are stored as sequences of words
    terms: List[Tuple[int, ...]] = field(default_factory=list)
    definitions: List[Tuple[int, ...]] = field(default_factory=list)

    # inverted indices
    _casefold_indices: Dict[str, Set[int]] = field(default_factory=dict)  # word -> word indices
    _term_indices: List[Set[int]] = field(default_factory=list)  # word_index -> term indices
    _def_indices: List[Set[int]] = field(default_factory=list)  # word_index -> def indices

    def __post_init__(self):
        assert self._resolve_word_index(' ') == 0

    def _resolve_word_index(self, word: str) -> int:
        # return if known word
        if word in self._vocab_indices:
            return self._vocab_indices[word]

        # add unknown word
        assert isinstance(word, str), word
        _idx = self._vocab_indices[word] = len(self.vocabulary)
        self.vocabulary.append(word)
        self._casefold_indices.setdefault(word.casefold(), set()).add(_idx)
        self._term_indices.append(set())
        self._def_indices.append(set())

        # double-check invariants before returning
        assert len(self._vocab_indices) == len(self.vocabulary) == _idx + 1
        assert len(self._term_indices) == len(self._def_indices) == _idx + 1
        assert self.vocabulary[_idx] == word, (self.vocabulary[_idx], word)  # check race condition
        return _idx

    def add_definition(self, term: str, definition: str) -> 'Dictionary':

        # tokenize
        term_words = list(unicode_tokenize(' '.join(term.strip().split())))
        def_words = list(unicode_tokenize(' '.join(definition.strip().split())))
        term_word_indices = tuple(self._resolve_word_index(token) for token in term_words)
        def_word_indices = tuple(self._resolve_word_index(token) for token in def_words)

        # add definition
        _idx = len(self.terms)
        self.terms.append(term_word_indices)
        self.definitions.append(def_word_indices)

        # add to index
        for word_index in term_word_indices:
            if word_index > 0:
                self._term_indices[word_index].add(_idx)
        for word_index in def_word_indices:
            if word_index > 0:
                self._def_indices[word_index].add(_idx)

        # allow operator chaining
        return self

    def _tuple_to_text(self, text_tuple):
        return ''.join(self.vocabulary[idx] for idx in text_tuple)

    def lookup_terms(self, text):
        matches = Counter()
        for word in unicode_tokenize(' '.join(text.strip().casefold().split())):
            for word_index in self._casefold_indices.get(word, set()):
                matches.update(self._term_indices[word_index])

        out = []
        for match_index, count in matches.most_common():
            out.append((''.join(self.vocabulary[idx] for idx in self.terms[match_index]),
                        ''.join(self.vocabulary[idx] for idx in self.definitions[match_index]),
                        count))
        return out

    def lookup_definitions(self, text):
        # normalize case and whitespace
        text = ' '.join(text.strip().casefold().split())

        matches = Counter()
        for word in unicode_tokenize(text):
            for word_index in self._casefold_indices.get(word, set()):
                matches.update(self._def_indices[word_index])

        out = []
        for match_index, count in matches.most_common():
            out.append((''.join(self.vocabulary[idx] for idx in self.terms[match_index]),
                        ''.join(self.vocabulary[idx] for idx in self.definitions[match_index]),
                        count))
        return out

    def term_words(self):
        return [self.vocabulary[word_idx]
                for word_idx, term_idx in enumerate(self._term_indices)
                if len(term_idx) > 0]

    def definition_words(self):
        return [self.vocabulary[word_idx]
                for word_idx, def_idx in enumerate(self._def_indices[1:])
                if len(def_idx) > 0]


@dataclass
class MultiDictionary:
    dictionaries: List[Dictionary] = field(default_factory=list)
    _casefold_index: Dict[str, Set[int]] = field(default_factory=dict)

    def add_dictionary(self, dictionary: Dictionary):
        _idx = len(self.dictionaries)
        self.dictionaries.append(dictionary)
        for word in dictionary.term_words():
            self._casefold_index.setdefault(word.casefold(), set()).add(_idx)
        for word in dictionary.definition_words():
            self._casefold_index.setdefault(word.casefold(), set()).add(_idx)

    def lookup_terms(self, text):
        dict_indices = set()
        for word in unicode_tokenize(' '.join(text.strip().casefold().split())):
            dict_indices.update(self._casefold_index.get(word, set()))

        out = []
        for dict_index in dict_indices:
            out.extend(self.dictionaries[dict_index].lookup_terms(text))
        return sorted(out, key=lambda x: x[-1], reverse=True)


@dataclass
class ApproxWordList:
    n_list: Tuple[int, ...]

    # vocabulary: word <-> word_index
    vocabulary: List[str] = field(default_factory=list)  # word_index -> word
    _vocab_indices: Dict[str, int] = field(default_factory=dict)  # word -> word_index

    # n-gram index (normalized vectors): n_gram -> [(word_index, norm_count), ...]
    n_gram_indices: Dict[int, Dict[str, List[Tuple[int, float]]]] = field(default_factory=dict)

    def _resolve_word_index(self, word: str) -> int:
        # return if known word
        if word in self._vocab_indices:
            return self._vocab_indices[word]

        # add unknown word
        assert isinstance(word, str), word
        _idx = self._vocab_indices[word] = len(self.vocabulary)
        self.vocabulary.append(word)

        # double-check invariants before returning
        assert len(self._vocab_indices) == len(self.vocabulary) == _idx + 1
        assert self.vocabulary[_idx] == word, (self.vocabulary[_idx], word)  # check race condition
        return _idx

    def add_word(self, word: str):
        if word in self._vocab_indices:
            return self

        for n in set(self.n_list):
            n_gram_index = self.n_gram_indices.setdefault(n, dict())
            word_index = self._resolve_word_index(word)
            n_gram_counter = Counter(text_n_grams(f'^{word}$', n=n))
            denominator = sum(count ** 2 for count in n_gram_counter.values()) ** 0.5
            for n_gram, count in n_gram_counter.most_common():
                n_gram_index.setdefault(n_gram, []).append((word_index, count / denominator))

        return self

    def lookup(self, word: str, top_k: Optional[int] = None, dim=1):
        matches: Dict[int, List[float]] = dict()
        for n_idx, n in enumerate(self.n_list):
            n_gram_counter = Counter(text_n_grams(f'^{word}$', n=n))
            denominator = sum(count ** 2 for count in n_gram_counter.values()) ** 0.5
            for n_gram, count in n_gram_counter.most_common():
                for word_index, norm_count in self.n_gram_indices[n].get(n_gram, []):
                    word_scores = matches.setdefault(word_index, [0 for _ in range(len(self.n_list))])
                    word_scores[n_idx] += norm_count * (count / denominator)  # cosine distance

        c = Counter({word_index: (sum(x ** dim for x in scores) / len(scores)) ** (1 / dim)
                     for word_index, scores in matches.items()})

        if top_k is None:
            top_k = len(matches)
        return [(self.vocabulary[word_index], round(match_score, 3)) for word_index, match_score in
                c.most_common(top_k)]


def emd_1d(locations_1: List[float], locations_2: List[float]) -> float:
    """
    distance needed to move
    """
    locations_1 = sorted(locations_1)
    locations_2 = sorted(locations_2)

    assert all(0 <= x <= 1 for x in locations_1)
    assert all(0 <= x <= 1 for x in locations_2)

    if len(locations_1) < len(locations_2):
        return emd_1d(locations_2, locations_1)

    elif len(locations_2) == 0:
        return len(locations_1)

    elif len(locations_1) == len(locations_2):
        # return sum((1 - 2 ** (-abs(l1 - l2) / max(locations_2))) for l1, l2 in zip(locations_1, locations_2))
        return sum(abs(l1 - l2) for l1, l2 in zip(locations_1, locations_2))

    else:
        return 1 + min(emd_1d(locations_1[:i] + locations_1[i + 1:], locations_2) for i in range(len(locations_1)))


def dameraulevenshtein(seq1, seq2):
    """Calculate the Damerau-Levenshtein distance between sequences.

    This distance is the number of additions, deletions, substitutions,
    and transpositions needed to transform the first sequence into the
    second. Although generally used with strings, any sequences of
    comparable objects will work.

    Transpositions are exchanges of *consecutive* characters; all other
    operations are self-explanatory.

    This implementation is O(N*M) time and O(M) space, for N and M the
    lengths of the two sequences.

    >>> dameraulevenshtein('ba', 'abc')
    2
    >>> dameraulevenshtein('fee', 'deed')
    2

    It works with arbitrary sequences too:
    >>> dameraulevenshtein('abcd', ['b', 'a', 'c', 'd', 'e'])
    2
    """
    # codesnippet:D0DE4716-B6E6-4161-9219-2903BF8F547F
    # Conceptually, this is based on a len(seq1) + 1 * len(seq2) + 1 matrix.
    # However, only the current and two previous rows are needed at once,
    # so we only store those.
    oneago = None
    thisrow = list(range(1, len(seq2) + 1)) + [0]
    for x in range(len(seq1)):
        # Python lists wrap around for negative indices, so put the
        # leftmost column at the *end* of the list. This matches with
        # the zero-indexed strings and saves extra calculation.
        twoago, oneago, thisrow = oneago, thisrow, [0] * len(seq2) + [x + 1]
        for y in range(len(seq2)):
            delcost = oneago[y] + 1
            addcost = thisrow[y - 1] + 1
            subcost = oneago[y - 1] + (seq1[x] != seq2[y])
            thisrow[y] = min(delcost, addcost, subcost)
            # This block deals with transpositions
            if (x > 0 and y > 0 and seq1[x] == seq2[y - 1]
                    and seq1[x - 1] == seq2[y] and seq1[x] != seq2[y]):
                thisrow[y] = min(thisrow[y], twoago[y - 2] + 1)
    return thisrow[len(seq2) - 1]


@dataclass
class ApproxWordList2:
    n_list: Tuple[int, ...]

    # vocabulary: word <-> word_index
    vocabulary: List[str] = field(default_factory=list)  # word_index -> word
    _vocab_indices: Dict[str, int] = field(default_factory=dict)  # word -> word_index

    # n-gram index (normalized vectors): n_gram -> [(word_index, (loc, loc, ...), ...]
    n_gram_indices: Dict[int, Dict[str, List[Tuple[int, Tuple[float, ...]]]]] = field(default_factory=dict)

    def _resolve_word_index(self, word: str) -> int:
        # return if known word
        if word in self._vocab_indices:
            return self._vocab_indices[word]

        # add unknown word
        assert isinstance(word, str), word
        _idx = self._vocab_indices[word] = len(self.vocabulary)
        self.vocabulary.append(word)

        # double-check invariants before returning
        assert len(self._vocab_indices) == len(self.vocabulary) == _idx + 1
        assert self.vocabulary[_idx] == word, (self.vocabulary[_idx], word)  # check race condition
        return _idx

    def add_word(self, word: str):
        if word in self._vocab_indices:
            return self

        for n in set(self.n_list):
            n_gram_index = self.n_gram_indices.setdefault(n, dict())
            word_index = self._resolve_word_index(word)

            n_grams = text_n_grams(f'^{word}$', n=n)
            n_gram_locations = dict()
            if len(n_grams) > 1:
                for idx, n_gram in enumerate(n_grams):
                    n_gram_locations.setdefault(n_gram, []).append(idx / (len(n_grams) - 1))
            elif n_grams:
                n_gram_locations.setdefault(n_grams[0], []).append(0)

            for n_gram, locations in n_gram_locations.items():
                n_gram_index.setdefault(n_gram, []).append((word_index, tuple(locations)))

        return self

    def lookup(self, word: str, top_k: Optional[int] = None, dim=1):
        matches: Dict[int, List[float]] = dict()
        for n_idx, n in enumerate(self.n_list):
            n_grams = text_n_grams(f'^{word}$', n=n)
            n_gram_locations = dict()
            for idx, n_gram in enumerate(n_grams):
                n_gram_locations.setdefault(n_gram, []).append(idx / (len(n_grams) - 1))

            for n_gram, locations in n_gram_locations.items():
                for other_word_index, other_locations in self.n_gram_indices[n].get(n_gram, []):
                    word_scores = matches.setdefault(other_word_index, [0 for _ in range(len(self.n_list))])
                    word_scores[n_idx] += max(len(locations), len(other_locations)) - emd_1d(locations, other_locations)

        c = Counter({word_index: (sum(x ** dim for x in scores) / len(scores)) ** (1 / dim)
                     for word_index, scores in matches.items()})

        if top_k is None:
            top_k = len(matches)
        return [(self.vocabulary[word_index], round(match_score, 3), dameraulevenshtein(word, self.vocabulary[word_index])) for word_index, match_score in
                c.most_common(top_k)]


if __name__ == '__main__':
    with open('../../dictionaries/words_ms.txt', encoding='utf8') as f:
        words = set(f.read().split())

    wl_1 = ApproxWordList2((1, 2, 3, 4))
    for word in words:
        wl_1.add_word(word)

    wl_2 = ApproxWordList2((2, 3, 4))
    for word in words:
        wl_2.add_word(word)

    wl_3 = ApproxWordList2((3, 4))
    for word in words:
        wl_3.add_word(word)

    wl_4 = ApproxWordList2((2, 4))
    for word in words:
        wl_4.add_word(word)

    with open('../../dictionaries/words_en.txt', encoding='utf8') as f:
        words = set(f.read().split())

    wl2_1 = ApproxWordList2((1, 2, 3, 4))
    for word in words:
        wl2_1.add_word(word)

    wl2_2 = ApproxWordList2((2, 3, 4))
    for word in words:
        wl2_2.add_word(word)

    wl2_3 = ApproxWordList2((3, 4))
    for word in words:
        wl2_3.add_word(word)

    wl2_4 = ApproxWordList2((2, 4))
    for word in words:
        wl2_4.add_word(word)

    while True:
        word = input('word:\n')
        word = word.strip()
        if not word:
            break
        print('wl_1', wl_1.lookup(word, 10))
        print('wl_2', wl_2.lookup(word, 10))
        print('wl_3', wl_3.lookup(word, 10))
        print('wl_4', wl_4.lookup(word, 10))
        print('wl2_1', wl2_1.lookup(word, 10))
        print('wl2_2', wl2_2.lookup(word, 10))
        print('wl2_3', wl2_3.lookup(word, 10))
        print('wl2_4', wl2_4.lookup(word, 10))
