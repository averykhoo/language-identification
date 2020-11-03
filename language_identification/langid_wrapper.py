from typing import Iterable
from typing import Optional

from langid import langid

from language_identification.preprocessing import check_languages
from language_identification.preprocessing import clean_text

SUPPORTED_LANGUAGES = sorted(['af', 'am', 'an', 'ar', 'as', 'az', 'be', 'bg', 'bn', 'br',
                              'bs', 'ca', 'cs', 'cy', 'da', 'de', 'dz', 'el', 'en', 'eo',
                              'es', 'et', 'eu', 'fa', 'fi', 'fo', 'fr', 'ga', 'gl', 'gu',
                              'he', 'hi', 'hr', 'ht', 'hu', 'hy', 'id', 'is', 'it', 'ja',
                              'jv', 'ka', 'kk', 'km', 'kn', 'ko', 'ku', 'ky', 'la', 'lb',
                              'lo', 'lt', 'lv', 'mg', 'mk', 'ml', 'mn', 'mr', 'ms', 'mt',
                              'nb', 'ne', 'nl', 'nn', 'no', 'oc', 'or', 'pa', 'pl', 'ps',
                              'pt', 'qu', 'ro', 'ru', 'rw', 'se', 'si', 'sk', 'sl', 'sq',
                              'sr', 'sv', 'sw', 'ta', 'te', 'th', 'tl', 'tr', 'ug', 'uk',
                              'ur', 'vi', 'vo', 'wa', 'xh', 'zh', 'zu'])  # 97 languages

# create langid model with normalized probabilities, then (optionally) set languages)
langid_model = langid.LanguageIdentifier.from_modelstring(langid.model, norm_probs=True)


def detect_language(text: str, language_codes: Optional[Iterable[str]] = None):
    language_codes = check_languages(language_codes, SUPPORTED_LANGUAGES)
    langid_model.set_languages(language_codes)
    return langid_model.rank(clean_text(text))
