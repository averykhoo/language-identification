import json
import re
from collections import Counter
from dataclasses import dataclass
from dataclasses import field
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Pattern
from typing import Set
from typing import Tuple
from typing import Union

import unicodedata

from tokenizer import text_n_grams
from tokenizer import unicode_tokenize

unicode_category_mapping = {
    'Lu': {'Lu'},  # Uppercase_Letter
    'Ll': {'Ll'},  # Lowercase_Letter
    'Lt': {'Lt'},  # Titlecase_Letter
    'LC': {'Lu', 'Ll', 'Lt'},  # Cased_Letter
    'Lm': {'Lm'},  # Modifier_Letter
    'Lo': {'Lo'},  # Other_Letter
    'L':  {'Lu', 'Ll', 'Lt', 'Lm', 'Lo'},  # Letter
    'L*': {'Lu', 'Ll', 'Lt', 'Lm', 'Lo'},  # Letter
    'Mn': {'Mn'},  # Nonspacing_Mark
    'Mc': {'Mc'},  # Spacing_Mark
    'Me': {'Me'},  # Enclosing_Mark
    'M':  {'Mn', 'Mc', 'Me'},  # Mark
    'M*': {'Mn', 'Mc', 'Me'},  # Mark
    'Nd': {'Nd'},  # Decimal_Number
    'Nl': {'Nl'},  # Letter_Number
    'No': {'No'},  # Other_Number
    'N':  {'Nd', 'Nl', 'No'},  # Number
    'N*': {'Nd', 'Nl', 'No'},  # Number
    'Pc': {'Pc'},  # Connector_Punctuation
    'Pd': {'Pd'},  # Dash_Punctuation
    'Ps': {'Ps'},  # Open_Punctuation
    'Pe': {'Pe'},  # Close_Punctuation
    'Pi': {'Pi'},  # Initial_Punctuation
    'Pf': {'Pf'},  # Final_Punctuation
    'Po': {'Po'},  # Other_Punctuation
    'P':  {'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po'},  # Punctuation
    'P*': {'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Pf', 'Po'},  # Punctuation
    'Sm': {'Sm'},  # Math_Symbol
    'Sc': {'Sc'},  # Currency_Symbol
    'Sk': {'Sk'},  # Modifier_Symbol
    'So': {'So'},  # Other_Symbol
    'S':  {'Sm', 'Sc', 'Sk', 'So'},  # Symbol
    'S*': {'Sm', 'Sc', 'Sk', 'So'},  # Symbol
    'Zs': {'Zs'},  # Space_Separator
    'Zl': {'Zl'},  # Line_Separator
    'Zp': {'Zp'},  # Paragraph_Separator
    'Z':  {'Zs', 'Zl', 'Zp'},  # Separator
    'Z*': {'Zs', 'Zl', 'Zp'},  # Separator
    'Cc': {'Cc'},  # Control
    'Cf': {'Cf'},  # Format
    'Cs': {'Cs'},  # Surrogate
    'Co': {'Co'},  # Private_Use
    'Cn': {'Cn'},  # Unassigned
    'C':  {'Cc', 'Cf', 'Cs', 'Co', 'Cn'},  # Other
    'C*': {'Cc', 'Cf', 'Cs', 'Co', 'Cn'},  # Other
}


@dataclass(frozen=True)
class CharSet:
    chars: Set[str] = field(default_factory=set)
    name: Optional[str] = field(default=None, compare=False, hash=False)

    def __post_init__(self):
        # check name
        if self.name is not None:
            if not isinstance(self.name, str):
                raise TypeError(self.name)
            if len(self.name) == 0:
                raise ValueError(self.name)

        # check type of provided set
        if not isinstance(self.chars, set):
            raise TypeError(self.chars)

        # check all the chars that were added
        _chars = set()
        for char in self.chars:
            if isinstance(char, str):
                if len(char) != 1:
                    raise ValueError(char)
                _chars.add(char)

            elif isinstance(char, int):
                if not 0 <= char <= 0x10FFFF:
                    raise ValueError(char)
                _chars.add(chr(char))  # we just converted an int into a char
                _modified = True  # so we must update self.chars later

            else:
                raise TypeError(char)

        # ALWAYS update the internal set just to make sure it's not referenced by someone else
        self.chars.clear()
        self.chars.update(_chars)

    @classmethod
    def from_ranges(cls,
                    unicode_ranges: Iterable[Tuple[int, int]],
                    name: Optional[str] = None) -> 'CharSet':
        out = CharSet(name=name)
        for range_start, range_end in unicode_ranges:
            out.add_range(range_start, range_end)
        return out

    @property
    def pattern(self) -> Pattern:
        return re.compile(f'{self.to_regex()}+', flags=re.U)

    @property
    def ranges(self) -> List[Tuple[int, int]]:
        code_points_iter = iter(sorted(map(ord, self.chars)))
        out = []

        range_start = range_end = next(code_points_iter)
        for code_point in code_points_iter:
            if range_end + 1 == code_point:
                range_end = code_point
            else:
                out.append((range_start, range_end))
                range_start = range_end = code_point
        out.append((range_start, range_end))
        return out

    def __iter__(self) -> Iterable[str]:
        return iter(self.chars)

    def __contains__(self, chars: Union[str, int]) -> bool:
        """
        we can't use lru_cache here, because self is not hashable
        we can't even use an instance-internal cache, because self.chars is mutable
        """
        if isinstance(chars, str):
            if len(chars) == 0:
                raise ValueError(chars)
            return all(char in self.chars for char in chars)

        elif isinstance(chars, int):
            if not 0 <= chars <= 0x10FFFF:
                raise ValueError(chars)
            return chr(chars) in self.chars

        else:
            raise TypeError

    def add(self, char: Union[str, int]) -> 'CharSet':
        # add a char
        if isinstance(char, str):
            if len(char) != 1:
                raise ValueError(char)
            self.chars.add(char)

        # convert from int
        elif isinstance(char, int):
            if not 0 <= char <= 0xFFFF:
                raise ValueError(char)
            self.chars.add(chr(char))

        # unknown type
        else:
            raise TypeError(char)

        # for operator chaining
        return self

    def remove(self, char: Union[str, int]) -> 'CharSet':
        # remove char
        if isinstance(char, str):
            if len(char) != 1:
                raise ValueError(char)
            self.chars.remove(char)

        # convert from int
        elif isinstance(char, int):
            if not 0 <= char <= 0xFFFF:
                raise ValueError(char)
            self.chars.remove(chr(char))

        # unknown type
        else:
            raise TypeError(char)

        # for operator chaining
        return self

    def discard(self, char: Union[str, int]) -> 'CharSet':
        # discard char if it exists
        if isinstance(char, str):
            if len(char) != 1:
                raise ValueError(char)
            self.chars.discard(char)

        # convert from int
        elif isinstance(char, int):
            if not 0 <= char <= 0xFFFF:
                raise ValueError(char)
            self.chars.discard(chr(char))

        # unknown type
        else:
            raise TypeError(char)

        # for operator chaining
        return self

    def copy(self) -> 'CharSet':
        return CharSet().update(self)

    def clear(self) -> 'CharSet':
        self.chars.clear()
        return self

    def add_range(self, range_start: Union[str, int], range_end: Union[str, int]) -> 'CharSet':
        # make sure range_start is an int
        if isinstance(range_start, str):
            if len(range_start) != 1:
                raise ValueError(range_start)
            range_start = ord(range_start)
        elif not isinstance(range_start, int):
            raise TypeError(range_start)

        # make sure range_end is an int
        if isinstance(range_end, str):
            if len(range_end) != 1:
                raise ValueError(range_end)
            range_end = ord(range_end)
        elif not isinstance(range_end, int):
            raise TypeError(range_end)

        # check that the range is within the unicode planes
        if range_start < 0:
            raise ValueError(range_start)
        if range_end > 0x10FFFF:
            raise ValueError(range_end)

        # check that the range is non-negative
        if range_end < range_start:
            raise ValueError(f'range is backwards ({range_start} -> {range_end})')

        # add each char
        self.chars.update(chr(code_point) for code_point in range(range_start, range_end + 1))

        # for operator chaining
        return self

    def update(self, other: Iterable[Union[str, int]]) -> 'CharSet':
        # update from other directly since we know a CharSet only contains chas
        if isinstance(other, CharSet):
            self.chars.update(other.chars)

        # create a temporary CharSet so that the update is atomic
        elif isinstance(other, Iterable):
            _other = CharSet()
            for char in other:
                _other.add(char)
            self.chars.update(_other.chars)

        # unknown type
        else:
            raise TypeError(other)

        # for operator chaining
        return self

    def intersection_update(self, other: Iterable[Union[str, int]]) -> 'CharSet':
        # intersect other directly
        if isinstance(other, CharSet):
            self.chars.intersection_update(other.chars)

        # create a temporary CharSet so that the change is atomic
        elif isinstance(other, Iterable):
            _other = CharSet()
            for char in other:
                _other.add(char)
            self.chars.intersection_update(_other)

        # unknown type
        else:
            raise TypeError(other)

        # for operator chaining
        return self

    def difference_update(self, other: Iterable[Union[str, int]]) -> 'CharSet':
        # intersect other directly
        if isinstance(other, CharSet):
            self.chars.difference_update(other.chars)

        # create a temporary CharSet so that the change is atomic
        elif isinstance(other, Iterable):
            _other = CharSet()
            for char in other:
                _other.add(char)
            self.chars.difference_update(_other)

        # unknown type
        else:
            raise TypeError(other)

        # for operator chaining
        return self

    def symmetric_difference_update(self, other: Iterable[Union[str, int]]) -> 'CharSet':
        # intersect other directly
        if isinstance(other, CharSet):
            self.chars.symmetric_difference_update(other.chars)

        # create a temporary CharSet so that the change is atomic
        elif isinstance(other, Iterable):
            _other = CharSet()
            for char in other:
                _other.add(char)
            self.chars.symmetric_difference_update(_other)

        # unknown type
        else:
            raise TypeError(other)

        # for operator chaining
        return self

    def union(self, other: Iterable[Union[str, int]]) -> 'CharSet':
        return CharSet().update(self).update(other)

    def intersection(self, other: Iterable[Union[str, int]]) -> 'CharSet':
        return CharSet().update(self).intersection_update(other)

    def difference(self, other: Iterable[Union[str, int]]) -> 'CharSet':
        return CharSet().update(self).difference_update(other)

    def symmetric_difference(self, other: Iterable[Union[str, int]]) -> 'CharSet':
        return CharSet().update(self).symmetric_difference_update(other)

    def isdisjoint(self, other: 'CharSet') -> bool:
        if not isinstance(other, CharSet):
            raise TypeError
        return self.chars.isdisjoint(other.chars)

    def issubset(self, other: 'CharSet') -> bool:
        if not isinstance(other, CharSet):
            raise TypeError
        return self.chars.issubset(other.chars)

    def issuperset(self, other: 'CharSet') -> bool:
        if not isinstance(other, CharSet):
            raise TypeError
        return self.chars.issuperset(other.chars)

    def pop(self) -> str:
        return self.chars.pop()

    def filter(self,
               filter_func: Union[Callable, str, Iterable[str]],
               *,
               inplace: bool = False,
               invert: bool = False,
               ) -> 'CharSet':
        """
        charset2 = charset.filter({'L*',  # letters
                                   'M*',  # diacritics, etc
                                   'N*',  # numbers
                                   'Co',  # private use char class
                                   })

        charset3 = charset2.filter('N*', invert=True)  # remove numbers
        """

        # create a new object if not inplace
        if not inplace:
            return self.copy().filter(filter_func, inplace=True, invert=invert)

        # is a func
        if isinstance(filter_func, Callable):
            if filter_func('\0') not in {True, False}:
                raise TypeError(filter_func)

        # is a string (unicode category)
        elif isinstance(filter_func, str):
            if filter_func not in unicode_category_mapping:
                raise ValueError(filter_func)

            _categories = unicode_category_mapping[filter_func]

            def filter_func(char):
                return unicodedata.category(char) in _categories

        # is a set of strings (unicode categories)
        elif isinstance(filter_func, Iterable):
            _categories = set()

            for elem in filter_func:
                if not isinstance(elem, str):
                    raise TypeError((elem, filter_func))
                if elem not in unicode_category_mapping:
                    raise ValueError((elem, filter_func))
                _categories.update(unicode_category_mapping[elem])

            def filter_func(char):
                return unicodedata.category(char) in _categories

        # unknown filter type
        else:
            raise TypeError(filter_func)

        # filter
        if not invert:
            _chars = set(char for char in self.chars if filter_func(char))
        else:
            _chars = set(char for char in self.chars if not filter_func(char))

        # update self
        self.chars.clear()
        self.chars.update(_chars)
        return self

    def to_regex(self) -> str:
        """
        create a regex pattern that matches exactly one char, e.g. r'[\x09\x0A\x0D\x20-\x7E]'
        """

        # turn a code point into escaped unicode
        def to_unicode(code_point: int) -> str:
            if code_point < 0:
                raise ValueError(code_point)
            elif code_point <= 0xFF:
                return f'\\x{code_point:02X}'
            elif code_point <= 0xFFFF:
                return f'\\u{code_point:04X}'
            elif code_point <= 0x10FFFF:  # max valid unicode char
                return f'\\U{code_point:08X}'
            else:
                raise ValueError(code_point)

        regex_parts = ['[']
        for range_start, range_end in self.ranges:
            regex_parts.append(to_unicode(range_start))
            if range_end > range_start:
                regex_parts.append('-')
                regex_parts.append(to_unicode(range_end))

        regex_parts.append(']')
        return ''.join(regex_parts)

    def _find_all(self, text: str, pos=None, endpos=None) -> List[str]:
        if pos is None:
            pos = 0
        if endpos is None:
            endpos = len(text)
        return self.pattern.findall(text, pos, endpos)


@dataclass
class CharSetIndex:
    inverted_index: Dict[str, Set[int]] = field(default_factory=dict, init=False)
    charsets_names: List[str] = field(default_factory=list, init=False)

    def add(self, charset: CharSet, charset_name: Optional[str] = None):
        if not isinstance(charset, CharSet):
            raise TypeError(charset)

        # check name
        if charset_name is None:
            charset_name = charset.name
        if not isinstance(charset_name, str):
            raise TypeError(charset_name)
        if len(charset_name) == 0:
            raise ValueError(charset_name)

        # avoid dupe charsets
        assert charset_name not in self.charsets_names

        # add charset to seen
        charset_idx = len(self.charsets_names)
        self.charsets_names.append(charset_name)
        assert self.charsets_names[charset_idx] == charset_name

        # index the chars
        for char in charset:
            self.inverted_index.setdefault(char, set()).add(charset_idx)

    def lookup_char(self, char: str) -> List[str]:
        return sorted(self.charsets_names[idx] for idx in self.inverted_index.get(char, set()))

    def lookup_union(self, word: str) -> List[str]:
        out = Counter()
        for char in word:
            out.update(self.inverted_index.get(char, set()))
        return [self.charsets_names[idx] for idx, count in out.most_common()]

    def lookup_intersection(self, word: str) -> List[str]:
        out = set(range(len(self.charsets_names)))
        for char in word:
            out.intersection_update(self.inverted_index.get(char, set()))
        return [self.charsets_names[idx] for idx in out]


class MultiCharSet:
    def __init__(self, *charsets: CharSet):
        for charset in charsets:
            assert isinstance(charset, CharSet)
        self.charsets = list(charsets)

    @classmethod
    def from_json(cls, path) -> 'MultiCharSet':
        out = MultiCharSet()
        with open(path, encoding='ascii') as f:
            data = json.load(f)
            for charset_name in sorted(data.keys()):
                out.add(CharSet.from_ranges(data[charset_name], name=charset_name))
        return out

    @property
    def pattern(self) -> Pattern:
        return re.compile('|'.join(f'{charset.to_regex()}+' for charset in self.charsets), flags=re.U)

    def __contains__(self, item):
        return any(item in charset for charset in self.charsets)

    def add(self, charset):
        if not isinstance(charset, CharSet):
            raise TypeError(charset)
        self.charsets.append(charset)
        return self

    def _find_all(self, text: str, pos=None, endpos=None) -> List[str]:
        if pos is None:
            pos = 0
        if endpos is None:
            endpos = len(text)
        return self.pattern.findall(text, pos, endpos)

    def build_index(self) -> CharSetIndex:
        index = CharSetIndex()
        for charset in self.charsets:
            index.add(charset)
        return index

    def to_json(self, path: Optional[str]):
        out = dict()
        for i, charset in enumerate(self.charsets):
            if charset.name is None:
                out[f'charset_{i}'] = charset.ranges
            else:
                out[charset.name] = charset.ranges

        if path is not None:
            with open(path, 'w', encoding='ascii') as f:
                json.dump(out, f, indent=4, ensure_ascii=False)

        return json.dumps(out, indent=4, ensure_ascii=False)


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
        matches = Counter()
        for word in unicode_tokenize(' '.join(text.strip().casefold().split())):
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
                    word_scores[n_idx] += norm_count * (count / denominator)

        c = Counter({word_index: (sum(x ** dim for x in scores) / len(scores)) ** (1 / dim)
                     for word_index, scores in matches.items()})

        if top_k is None:
            top_k = len(matches)
        return [(self.vocabulary[word_index], round(match_score, 3)) for word_index, match_score in
                c.most_common(top_k)]


if __name__ == '__main__':
    with open('dictionaries/words_ms.txt', encoding='utf8') as f:
        words = set(f.read().split())

    wl_1 = ApproxWordList((2, 3, 4))
    for word in words:
        wl_1.add_word(word)

    wl_2 = ApproxWordList((2,))
    for word in words:
        wl_2.add_word(word)

    wl_3 = ApproxWordList((3,))
    for word in words:
        wl_3.add_word(word)

    wl_4 = ApproxWordList((4,))
    for word in words:
        wl_4.add_word(word)

    with open('dictionaries/words_en.txt', encoding='utf8') as f:
        words = set(f.read().split())

    wl2_1 = ApproxWordList((2, 3, 4))
    for word in words:
        wl2_1.add_word(word)

    wl2_2 = ApproxWordList((2,))
    for word in words:
        wl2_2.add_word(word)

    wl2_3 = ApproxWordList((3,))
    for word in words:
        wl2_3.add_word(word)

    wl2_4 = ApproxWordList((4,))
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
