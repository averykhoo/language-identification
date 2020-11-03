from typing import Iterable
from typing import Optional

import cld2
import cld2full

from language_identification.preprocessing import check_languages

SUPPORTED_LANGUAGES = sorted(lang_code.decode('ascii').split('-')[0] for lang_name, lang_code in cld2.LANGUAGES)


def detect_language(text: str, language_codes: Optional[Iterable[str]] = None, use_cld2full: bool = False):
    language_codes=check_languages(language_codes, SUPPORTED_LANGUAGES)

    if use_cld2full:
        is_reliable, bytes_found, details = cld2full.detect(text, bestEffort=True)
    else:
        is_reliable, bytes_found, details = cld2.detect(text, bestEffort=True)

    if not is_reliable:
        return []

    out = []
    for language_name, language_code, percent, score in details:
        if '-' in language_code:
            language_code = language_code.split('-')[0]
        if language_code not in language_codes:
            continue
        if score < 1:
            continue
        if percent < 50:
            continue
        if use_cld2full:
            out.append((language_code, score / 500))
        else:
            out.append((language_code, score / 1000))

    return sorted(out, key=lambda x: x[1:], reverse=True)
