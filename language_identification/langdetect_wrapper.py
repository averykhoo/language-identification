from typing import Iterable
from typing import Optional

import langdetect

from language_identification.preprocessing import check_languages
from language_identification.preprocessing import clean_text

SUPPORTED_LANGUAGES = sorted(['af', 'ar', 'bg', 'bn', 'ca', 'cs', 'cy', 'da', 'de', 'el',
                              'en', 'es', 'et', 'fa', 'fi', 'fr', 'gu', 'he', 'hi', 'hr',
                              'hu', 'id', 'it', 'ja', 'kn', 'ko', 'lt', 'lv', 'mk', 'ml',
                              'mr', 'ne', 'nl', 'no', 'pa', 'pl', 'pt', 'ro', 'ru', 'sk',
                              'sl', 'so', 'sq', 'sv', 'sw', 'ta', 'te', 'th', 'tl', 'tr',
                              'uk', 'ur', 'vi', 'zh'])


def detect_language(text: str, language_codes: Optional[Iterable[str]] = None):
    language_codes = check_languages(language_codes, SUPPORTED_LANGUAGES)

    results = [(res.lang.split('-')[0], res.prob) for res in langdetect.detect_langs(clean_text(text))]
    return [(lang, prob) for lang, prob in results if lang in language_codes]
