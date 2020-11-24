import re
from dataclasses import dataclass
from dataclasses import field
from typing import Callable
from typing import Iterable
from typing import List
from typing import Pattern
from typing import Set
from typing import Tuple
from typing import Union

import unicodedata

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

    def __post_init__(self):
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

        # # remove the constructor
        # object.__delattr__(self, 'from_ranges')

    @classmethod
    def from_ranges(cls, unicode_ranges: Iterable[Tuple[int, int]]) -> 'CharSet':
        out = CharSet()
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


class MultiCharSet:
    def __init__(self, *charsets: CharSet):
        for charset in charsets:
            assert isinstance(charset, CharSet)
        self.charsets = list(charsets)

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
