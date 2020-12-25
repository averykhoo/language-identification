from collections import Counter
from dataclasses import dataclass
from dataclasses import field
from functools import lru_cache
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Union

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


@lru_cache(maxsize=0xFFFF)
def _emd_1d(locations_1: Tuple[float], locations_2: Tuple[float]) -> float:
    if len(locations_1) == len(locations_2):
        return sum(abs(l1 - l2) for l1, l2 in zip(locations_1, locations_2))

    elif len(locations_2) == 1:
        return len(locations_1) - 1 + min(abs(l1 - locations_2[0]) for l1 in locations_1)

    else:
        # noinspection PyTypeChecker
        return 1 + min(_emd_1d(locations_1[:i] + locations_1[i + 1:], locations_2) for i in range(len(locations_1)))


def emd_1d_fast(locations_x: List[float], locations_y: List[float]) -> float:
    """
    distance needed to move
    todo: optimize worst case
    """
    assert all(0 <= x <= 1 for x in locations_x)
    assert all(0 <= x <= 1 for x in locations_y)

    # locations_1 will be the longer list
    if len(locations_x) < len(locations_y):
        locations_x, locations_y = locations_y, locations_x

    # empty list, so just count the l1 items and exit early
    if len(locations_y) == 0:
        return len(locations_x)

    # only one item, so take min distance and count the rest of the l1 items
    if len(locations_y) == 1:
        return min(abs(l1 - locations_y[0]) for l1 in locations_x) + len(locations_x) - 1

    # make a COPY of the list, sorted in reverse (descending order)
    # we'll be modifying in-place later, and we don't want to update the input
    locations_x = sorted(locations_x, reverse=True)
    locations_y = sorted(locations_y, reverse=True)

    # accumulated distance as we simplify the problem
    acc = 0

    # greedy-match constrained points with only one possible match (at the smaller end of locations_y)
    while locations_y and locations_x:
        if locations_y[-1] <= locations_x[-1]:
            acc += locations_x.pop(-1) - locations_y.pop(-1)
        elif len(locations_x) >= 2 and (locations_y[-1] - locations_x[-1]) <= (locations_x[-2] - locations_y[-1]):
            acc += locations_y.pop(-1) - locations_x.pop(-1)
        else:
            break

    # reverse both lists IN PLACE, so now they are sorted in ascending order
    locations_x.reverse()
    locations_y.reverse()

    # greedy-match constrained points with only one possible match (at the larger end of locations_y)
    while locations_y and locations_x:
        if locations_y[-1] >= locations_x[-1]:
            acc += locations_y.pop(-1) - locations_x.pop(-1)
        elif len(locations_x) >= 2 and (locations_x[-1] - locations_y[-1]) <= (locations_y[-1] - locations_x[-2]):
            acc += locations_x.pop(-1) - locations_y.pop(-1)
        else:
            break

    # another chance to early exit
    if len(locations_y) == 0:
        return acc + len(locations_x)
    if len(locations_y) == 1:
        return acc + min(abs(l1 - locations_y[0]) for l1 in locations_x) + len(locations_x) - 1

    # todo: build the bipartite graph
    # backward and forward pass

    # todo: remove all unmatchable points from the graph
    # [y1 x1 x2 x3 y2] ==> x2 can never be matched

    # todo: greedy-match unshared points
    # [x1 y1 ... x2 ...]       ==> if x1y1 < y1x2, then y1 -> x1
    # [... x3 x4 y1 x5 x6 ...] ==> y1 can only match x4 or x5 (assuming there are no y-chains)

    return _emd_1d(tuple(sorted(locations_x)), tuple(sorted(locations_y)))


def emd_1d_slow(locations_x: List[float], locations_y: List[float]) -> float:

    # locations_1 will be the longer list
    if len(locations_x) < len(locations_y):
        return emd_1d_slow(locations_y, locations_x)

    #
    if len(locations_x) == len(locations_y):
        return sum(abs(l1 - l2) for l1, l2 in zip(sorted(locations_x), sorted(locations_y)))

    return 1 + min(emd_1d_slow(locations_x[:i] + locations_x[i + 1:], locations_y) for i in range(len(locations_x)))


def emd_1d(locations_x: List[float], locations_y: List[float]) -> float:
    assert all(0 <= x <= 1 for x in locations_x)
    assert all(0 <= x <= 1 for x in locations_y)

    answer_1 = emd_1d_slow(locations_x, locations_y)
    answer_2 = emd_1d_fast(locations_x, locations_y)
    assert answer_1 == answer_2
    return answer_2


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
        return [
            (self.vocabulary[word_index], round(match_score, 3), dameraulevenshtein(word, self.vocabulary[word_index]))
            for word_index, match_score in
            c.most_common(top_k)]


def levenshteinDistance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2 + 1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]


class ApproxWordList3:
    def __init__(self, n: Union[int, Iterable[int]] = (2, 4), case_sensitive: bool = False):
        if isinstance(n, int):
            self.__n_list = (n,)
        elif isinstance(n, Iterable):
            self.__n_list = tuple(n)
        else:
            raise TypeError(n)

        # vocabulary: word <-> word_index
        self.__vocabulary: List[str] = []  # word_index -> word
        self.__vocab_indices: Dict[str, int] = dict()  # word -> word_index

        # n-gram index (normalized vectors): n_gram -> [(word_index, (loc, loc, ...)), ...]
        self.__n_gram_indices: Dict[str, List[Tuple[int, Tuple[float, ...]]]] = dict()

        # case sensitivity
        if not isinstance(case_sensitive, (bool, int)):
            raise TypeError(case_sensitive)
        self.__case_insensitive = not case_sensitive

    @property
    def vocabulary(self) -> List[str]:
        return sorted(self.vocabulary)

    def _resolve_word_index(self, word: str, auto_add=True) -> Optional[int]:
        if not isinstance(word, str):
            raise TypeError(word)
        if len(word) == 0:
            raise ValueError(word)

        # a bit like lowercase, but more consistent for arbitrary unicode
        if self.__case_insensitive:
            word = word.casefold()

        # return if known word
        if word in self.__vocab_indices:
            return self.__vocab_indices[word]

        # do we want to add it to the vocabulary
        if not auto_add:
            return None

        # add unknown word
        _idx = self.__vocab_indices[word] = len(self.__vocabulary)
        self.__vocabulary.append(word)

        # double-check invariants before returning
        assert len(self.__vocab_indices) == len(self.__vocabulary) == _idx + 1
        assert self.__vocabulary[_idx] == word, (self.__vocabulary[_idx], word)  # check race condition
        return _idx

    def add_word(self, word: str):
        if not isinstance(word, str):
            raise TypeError(word)
        if len(word) == 0:
            raise ValueError(word)

        if self.__case_insensitive:
            word = word.casefold()

        # already contained, nothing to add
        if word in self.__vocab_indices:
            return self

        # i'll be using the STX and ETX control chars as START_TEXT and END_TEXT flags
        assert '\2' not in word and '\3' not in word, word

        word_index = self._resolve_word_index(word)

        for n in set(self.__n_list):
            if n > 1:
                # add START_TEXT and END_TEXT flags
                n_grams = [f'\2{word}\3'[i:i + n] for i in range(len(word) - n + 3)]
            else:
                # do not add START_TEXT and END_TEXT flags for 1-grams
                n_grams = list(word)

            n_gram_locations = dict()  # n_gram -> [loc, loc, ...]
            if len(n_grams) > 1:
                for idx, n_gram in enumerate(n_grams):
                    n_gram_locations.setdefault(n_gram, []).append(idx / (len(n_grams) - 1))
            elif n_grams:
                n_gram_locations.setdefault(n_grams[0], []).append(0)

            for n_gram, locations in n_gram_locations.items():
                self.__n_gram_indices.setdefault(n_gram, []).append((word_index, tuple(locations)))

        return self

    def __lookup(self, word: str, dim: Union[int, float] = 1) -> Counter:
        # count matching n-grams
        matches: Dict[int, List[float]] = dict()
        for n_idx, n in enumerate(self.__n_list):
            n_grams = [f'\2{word}\3'[i:i + n] for i in range(len(word) - n + 3)]
            n_gram_locations = dict()
            for idx, n_gram in enumerate(n_grams):
                n_gram_locations.setdefault(n_gram, []).append(idx / (len(n_grams) - 1))

            for n_gram, locations in n_gram_locations.items():
                for other_word_index, other_locations in self.__n_gram_indices.get(n_gram, []):
                    word_scores = matches.setdefault(other_word_index, [0 for _ in range(len(self.__n_list))])
                    word_scores[n_idx] += max(len(locations), len(other_locations)) - emd_1d(locations, other_locations)

        # normalize scores
        for other_word_index, word_scores in matches.items():
            norm_scores = [word_scores[n_idx] / (len(word) - n + 3) for n_idx, n in enumerate(self.__n_list)]
            matches[other_word_index] = norm_scores

        # average the similarity scores
        return Counter({word_index: (sum(x ** dim for x in scores) / len(scores)) ** (1 / dim)
                        for word_index, scores in matches.items()})

    def lookup(self, word: str, top_k: int = 10, dim: Union[int, float] = 1):
        if not isinstance(word, str):
            raise TypeError(word)
        if len(word) == 0:
            raise ValueError(word)

        if self.__case_insensitive:
            word = word.casefold()

        assert '\2' not in word and '\3' not in word, word

        # average the similarity scores
        counter = self.__lookup(word, dim)
        _, top_score = counter.most_common(1)[0]

        # return only top_k results if specified (and non-zero), otherwise return all results
        if not top_k or top_k < 0:
            top_k = len(counter)

        # also return edit distances for debugging
        out = [(self.__vocabulary[word_index], round(match_score, 3),
                dameraulevenshtein(word, self.__vocabulary[word_index]),
                levenshteinDistance(word, self.__vocabulary[word_index]),
                )
               for word_index, match_score in counter.most_common(top_k * 2)
               if (match_score >= top_score * 0.9) or dameraulevenshtein(word, self.__vocabulary[word_index]) <= 1]

        return out[:top_k]


def n_gram_emd(word_1: str, word_2: str, n: int = 2):
    """
    optimized for readability, not speed
    test cases: https://www.watercoolertrivia.com/blog/schwarzenegger
    """

    assert isinstance(word_1, str) and '\2' not in word_1 and '\3' not in word_1
    assert isinstance(word_2, str) and '\2' not in word_2 and '\3' not in word_2
    assert isinstance(n, int) and n >= 2

    n_grams_1 = [f'\2{word_1}\3'[i:i + n] for i in range(len(word_1) - n + 3)]
    n_grams_2 = [f'\2{word_2}\3'[i:i + n] for i in range(len(word_2) - n + 3)]

    n_gram_locations_1 = dict()
    for idx, n_gram in enumerate(n_grams_1):
        n_gram_locations_1.setdefault(n_gram, []).append(idx / (len(n_grams_1) - 1))

    n_gram_locations_2 = dict()
    for idx, n_gram in enumerate(n_grams_2):
        n_gram_locations_2.setdefault(n_gram, []).append(idx / (len(n_grams_2) - 1))

    distance = 0
    total = 0
    for n_gram, locations in n_gram_locations_1.items():
        total += len(locations)
        if n_gram not in n_gram_locations_2:
            distance += len(locations)
    for n_gram, locations in n_gram_locations_2.items():
        total += len(locations)
        if n_gram not in n_gram_locations_1:
            distance += len(locations)
        else:
            print(n_gram, locations, n_gram_locations_1[n_gram])
            distance += emd_1d(locations, n_gram_locations_1[n_gram])

    return distance, total


if __name__ == '__main__':
    # with open('../../dictionaries/words_ms.txt', encoding='utf8') as f:
    #     words = set(f.read().split())
    # #
    # # wl_1 = ApproxWordList3((1, 2, 3, 4))
    # # for word in words:
    # #     wl_1.add_word(word)
    # #
    # # wl_2 = ApproxWordList3((2, 3, 4))
    # # for word in words:
    # #     wl_2.add_word(word)
    # #
    # # wl_3 = ApproxWordList3((3, 4))
    # # for word in words:
    # #     wl_3.add_word(word)
    #
    # wl_4 = ApproxWordList3((2, 4))
    # for word in words:
    #     wl_4.add_word(word)
    #
    # with open('../../dictionaries/words_en.txt', encoding='utf8') as f:
    #     words = set(f.read().split())
    #
    # # wl2_1 = ApproxWordList3((1, 2, 3, 4))
    # # for word in words:
    # #     wl2_1.add_word(word)
    # #
    # # wl2_2 = ApproxWordList3((2, 3, 4))
    # # for word in words:
    # #     wl2_2.add_word(word)
    # #
    # # wl2_3 = ApproxWordList3((3, 4))
    # # for word in words:
    # #     wl2_3.add_word(word)
    #
    # wl2_4 = ApproxWordList3((2, 4))
    # for word in words:
    #     wl2_4.add_word(word)
    #
    # print(wl_4.lookup('bananananaanananananana'))
    # print(wl2_4.lookup('bananananaanananananana'))
    #
    # while True:
    #     word = input('word:\n')
    #     word = word.strip()
    #     if not word:
    #         break
    #     # print('wl_1', wl_1.lookup(word))
    #     # print('wl_2', wl_2.lookup(word))
    #     # print('wl_3', wl_3.lookup(word))
    #     print('wl_4', wl_4.lookup(word))
    #     # print('wl2_1', wl2_1.lookup(word))
    #     # print('wl2_2', wl2_2.lookup(word))
    #     # print('wl2_3', wl2_3.lookup(word))
    #     print('wl2_4', wl2_4.lookup(word))
    a = [
        'Schwartzenegger',
        'Schwarzeneger',
        'Schwarzenager',
        'Schwartzenager',
        'Schwartzeneger',
        'Schwarzeneggar',
        'Schwarzenneger',
        'Swartzenegger',
        'Swarzenegger',
        'Schwarzenagger',
        'Schwarznegger',
        'Swartzenager',
        'Schwarzanegger',
        'Shwarzenegger',
        'Schwartzenagger',
        'Swartzeneger',
        'Schwartznegger',
        'Schwarzenegar',
        'Shwartzenegger',
        'Schwarzennegger',
        'Schwarzennager',
        'Schwartzanegger',
        'Schwartzenneger',
        'Schwarzanager',
        'Schwarzengger',
        'Schwarzennegar',
        'Shwartzeneger',
        'Schwartzeneggar',
        'Schwarzneger',
        'Schwarzneggar',
        'Schwartzenegar',
        'Schwartzneger',
        'Schwazenegger',
        'Shwartzenager',
        'Swartzanegger',
        'Swarzeneger',
        'Swarzeneggar',
        'Schwarenegger',
        'Schwartzennager',
        'Schwartzneggar',
        'Shwarzeneger',
        'Swartzeneggar',
        'Swartznegger',
        'Swarzenager',
        'Swarzenagger',
        'Scharzenegger',
        'Schwarnegger',
        'Schwartnegger',
        'Schwartzanager',
        'Schwartzaneger',
        'Schwartzinager',
        'Schwarzzenager',
        'Shwarzenager',
        'Swartzenagger',
        'Swartzineger',
        'Scharzeneger',
        'Schwarnzenegger',
        'Schwartenager',
        'Schwartenegar',
        'Schwarteneger',
        'Schwartnegar',
        'Schwartzanegar',
        'Schwartzenger',
        'Schwartzenggar',
        'Schwartzineger',
        'Schwartznager',
        'Schwarzaneger',
        'Schwarzaneggar',
        'Schwarzanger',
        'Schwarzenaeger',
        'Schwarzeniger',
        'Schwarzinager',
        'Schwarznager',
        'Schwarztenegger',
        'Schwarzzeneger',
        'Schwarzzenegger',
        'Schwazenager',
        'Schwazeneger',
        'Scwartzenegger',
        'Scwarzenegger',
        'Shwartznegger',
        'Shwarzenegar',
        'Swarteneger',
        'Swartzanager',
        'Swartznager',
        'Swartzneger',
        'Swarzanegger',
        'Swarzennager',
        'Swarzenneger',
        'Swazeneger',
        'Schartzenager',
        'Schartzennager',
        'Schartznager',
        'Scharwzeneger',
        'Scharzenager',
        'Schawarzneneger',
        'Schawrknegger',
        'Schazenegger',
        'Schneckenger',
        'Schrarznegger',
        'Schrawzenneger',
        'Schrwazeneggar',
        'Schrwazenegger',
        'Schrwtzanagger',
        'Schsargdneger',
        'Schwaranagger',
        'Schwararzenegger',
        'Schwarezenegger',
        'Schwarganzer',
        'Schwarnznegar',
        'Schwarsanegger',
        'Schwarsenagger',
        'Schwarsnegger',
        'Schwartaneger',
        'Schwartenagger',
        'Schwartenegger',
        'Schwartenneger',
        'Schwarterneger',
        'Schwartineger',
        'Schwartnager',
        'Schwartnehar',
        'Schwartsaneger',
        'Schwartsinager',
        'Schwartzaneggar',
        'Schwartzanger',
        'Schwartzeiojaweofjaweneger',
        'Schwartzenagar',
        'Schwartzenegget',
        'Schwartzeneiger',
        'Schwartzengar',
        'Schwartzenkangaroo',
        'Schwartzennegar',
        'Schwartzinagger',
        'Schwartzinegar',
        'Schwartziniger',
        'Schwartznagger',
        'Schwartznegar',
        'Schwarz',
        'Schwarzamegger',
        'Schwarzanagger',
        'Schwarzatwizzler',
        'Schwarzeggar',
        'Schwarzegger',
        'Schwarzenaega',
        'Schwarzenagher',
        'Schwarzeneeger',
        'Schwarzenegor',
        'Schwarzenenergy',
        'Schwarzengeggar',
        'Schwarzgenar',
        'Schwarzinagger',
        'Schwarzineggar',
        'Schwarztenegar',
        'Schwarzzanager',
        'Schwatzeneggar',
        'Schwatzenneger',
        'Schwazenaeger',
        'Schwazenegrr',
        'Schwazerneger',
        'Schwazinager',
        'Schwaznagger',
        'Schwazneger',
        'Schwaznnager',
        'Schwazzeneger',
        'Schwazzenger',
        'Schwazzinager',
        'Schzwarnegger',
        'Scwarrzenegger',
        'Scwarzenager',
        'Scwarzeneggar',
        'Scwarzenneger',
        'Scwharzanegger',
        'Scwharzeneggar',
        'Shwarsneger',
        'Shwartaneger',
        'Shwarteneger',
        'Shwartinznegar',
        'Shwartnierger',
        'Shwartsnagger',
        'Shwartzanager',
        'Shwartzanegar',
        'Shwartzaneger',
        'Shwartzanegger',
        'Shwartzenagor',
        'Shwartzeneggar',
        'Shwartzengar',
        'Shwartzennegar',
        'Shwartzganeger',
        'Shwartznager',
        'Shwartzneger',
        'Shwarzanegger',
        'Shwarzenagger',
        'Shwarzenneger',
        'Shwarznager',
        'Shwaztsinager',
        'Swarchneger',
        'Swarchzinager',
        'Swarchznegger',
        'Swartenager',
        'Swartenegger',
        'Swartenzager',
        'Swartiznager',
        'Swartschenager',
        'Swartseneger',
        'Swartseneggar',
        'Swartsenenger',
        'Swartshanaiger',
        'Swarttenegger',
        'Swartz.',
        'Swartzanagger',
        'Swartzaneger',
        'Swartzanegga',
        'Swartzeigner',
        'Swartzenagar',
        'Swartzeneagar',
        'Swartzenegar',
        'Swartzenegher',
        'Swartzengger',
        'Swartzennager',
        'Swartzennegar',
        'Swartzenneger',
        'Swartzerniger',
        'Swartzinager',
        'Swartzineggar',
        'Swartznagger',
        'Swartznegar',
        'Swartzneggar',
        'Swarzenaeger',
        'Swarzenaggar',
        'Swarzenaider',
        'Swarzengger',
        'Swarzneger',
        'Swarznegger',
        'Swarzshnegger',
        'Swarzzeneggar',
        'Swarzzenegger',
        'Swatgnezzer',
        'Swatz..',
        'Swatzinagger',
        'Swazenegger',
        'Swazernager',
        'Swchwartzignegeridknga',
        'Swchwazaneger',
        'Swertizager',
        'Swertzeneggar',
        'Swhartznegar',
        'Switzenagger',
        'Swiztinager',
        'Swuartzenegar',
        'Schwartzanagger',
        'Schwartzennnnnnn',
        'Schwarzenger',
        'Swartasenegger',
        'Swazenegar',
    ]
    b = 'Schwarzenegger'

    print(n_gram_emd('banana', 'bababanananananananana'))
    print(n_gram_emd('banana', 'bababanananananananananna'))
    # print(n_gram_emd('banana', 'bababananananananananannanananananananana'))
