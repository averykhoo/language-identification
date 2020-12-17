import json
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple

from language_identification.iso639_3 import iso639_2_1
from language_identification.preprocessing import check_languages
from language_identification.scripts_langid_datatypes import CharSet
from language_identification.scripts_langid_datatypes import CharSetIndex


def load(path):
    with open(path) as f:
        script_data = json.load(f)

    language_charsets = dict()
    for script_name in script_data.keys():
        script_langs = set(script_data[script_name]['langs'])
        script_charset = CharSet.from_ranges(script_data[script_name]['chars'])
        script_charset = script_charset.filter(['L*', 'M*'])  # letters and diacritics

        for lang in script_langs:
            language_charsets.setdefault(lang, CharSet()).update(script_charset)

    charset_index = CharSetIndex()
    for lang in sorted(language_charsets.keys()):
        charset_index.add(language_charsets[lang], iso639_2_1.get(lang, lang))  # iso639-2 to iso639-1 where possible

    return charset_index


_CHARSET_INDEX = load('scripts.json')
SUPPORTED_LANGUAGES = sorted(_CHARSET_INDEX.charsets_names)


# todo: probabilities should be exponential not linear
def detect_language(text: str, language_codes: Optional[Iterable[str]] = None) -> List[Tuple[str, float]]:
    language_codes = set(check_languages(language_codes, SUPPORTED_LANGUAGES))
    out = []
    total = 0

    # todo: iterate over Counter(text) to reduce duplicate lookups?
    for lang, fraction in _CHARSET_INDEX.lookup_fraction(text, True):
        if lang in language_codes:
            out.append((lang, fraction))
            total += fraction

    return [(lang, fraction / total) for lang, fraction in out]


if __name__ == '__main__':
    print(detect_language('日 月 木'))
    print(detect_language('カタカナ'))
    print(detect_language('片仮名'))
    print(detect_language('平仮名,ひらがな'))
    print(detect_language('平仮名'))
    print(detect_language('ひらがな'))
    print(detect_language('ㄱ ㄴ ㄷ ㄹ ㅁ'))
    print(detect_language('맏아들'))
