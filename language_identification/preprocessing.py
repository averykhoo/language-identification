import re
import warnings
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Union

import utils

# noinspection PyProtectedMember

BYTE_LENGTH_LIMIT = 10 * 1024 * 1024  # up to 10 MiB


def clean_text(text: str):
    if not isinstance(text, str):
        raise TypeError(text)

    text = utils.ensure_unicode(text)  # make sure it's proper unicode
    text = re.sub(r'\b\d+\b', '', text, flags=re.UNICODE)  # remove numbers
    text = re.sub(r'\s+', ' ', text, flags=re.UNICODE).strip()  # normalize whitespace

    if len(text) == 0:
        raise ValueError('no words provided')

    return text


def check_languages(specified_languages: Optional[Iterable[str]], supported_languages: Union[List[str], Set[str]]):
    if not specified_languages:
        return sorted(supported_languages)

    _language_codes = set()
    if not isinstance(specified_languages, Iterable):
        raise TypeError(specified_languages)
    language_codes = set(specified_languages)
    for lc in language_codes:
        if not isinstance(lc, str):
            raise TypeError(lc)
        if lc not in supported_languages:
            # warnings.warn(f'unsupported language {lc} will be ignored')
            continue
        _language_codes.add(lc)

    return _language_codes
