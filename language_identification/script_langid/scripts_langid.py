import json
import math
from collections import Counter
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple

from language_identification.iso639_3 import iso639_2_1
from language_identification.preprocessing import check_languages
from language_identification.script_langid.datatypes import CharSet
from language_identification.script_langid.datatypes import CharSetIndex
from tokenizer import unicode_tokenize


def load(path):
    with open(path) as f:
        script_data = json.load(f)

    language_charsets = dict()
    for script_name in script_data.keys():
        script_langs = set(script_data[script_name]['langs'])
        script_charset = CharSet.from_ranges(script_data[script_name]['chars'])
        script_charset = script_charset.filter(['L*', 'S*'])  # letters and symbols (no diacritics or numbers)

        for lang in script_langs:
            language_charsets.setdefault(lang, CharSet()).update(script_charset)

    charset_index = CharSetIndex()
    for lang in sorted(language_charsets.keys()):
        charset_index.add(language_charsets[lang], iso639_2_1.get(lang, lang))  # iso639-2 to iso639-1 where possible

    return charset_index


_CHARSET_INDEX = load('scripts.json')
SUPPORTED_LANGUAGES = sorted(_CHARSET_INDEX.charsets_names)


def detect_word(word: str) -> List[Tuple[str, float]]:
    out = []
    total = 0

    for lang, fraction in _CHARSET_INDEX.lookup_fraction(word):
        out.append((lang, fraction))
        total += fraction

    return [(lang, fraction / total) for lang, fraction in out]


def detect_language(text: str, language_codes: Optional[Iterable[str]] = None) -> List[Tuple[str, float]]:
    language_codes = set(check_languages(language_codes, SUPPORTED_LANGUAGES))
    scores = dict()
    cumulative = 0

    for word in unicode_tokenize(text):
        unseen = set(scores.keys())
        min_score = 0

        for lang, prob in detect_word(word):
            if lang in scores:
                scores[lang] += math.log2(prob)
                unseen.remove(lang)
            else:
                scores[lang] = cumulative + math.log2(prob)
            min_score = min(min_score, math.log2(prob))

        for lang in unseen:
            scores[lang] += min_score - math.log2(len(language_codes))

        cumulative += min_score - math.log2(len(language_codes))

    if not scores:
        return []

    max_score = max(scores.values())
    probs = Counter()
    total = 0
    for lang, score in scores.items():
        prob = 2 ** (score - max_score)
        total += prob
        probs[lang] = prob

    return [(lang, prob / total) for lang, prob in probs.most_common()]


if __name__ == '__main__':
    print(detect_language('日 月 木'))  # chinese
    print(detect_language('日 月 木 ㄈ'))  # chinese and bopo
    print(detect_language('平仮名'))  # japanese kanji
    print(detect_language('カタカナ'))  # japanese katakana
    print(detect_language('ひらがな'))  # japanese hiragana
    print(detect_language('平仮名, ひらがな'))  # mixed kanji / hira
    print(detect_language('ㄱ ㄴ ㄷ ㄹ ㅁ'))  # korean jamo
    print(detect_language('맏아들'))  # korean hangul
    print(detect_language('hello world'))  # latin chars
    print(detect_language('123'))  # numbers
    print(detect_language('ရှစ်လေးလုံးအရေးအခင်'))  # burmese
    print(detect_language('แหลงข้าหลวง'))  # thai
    print(detect_language('\u0627\u0644\u0639\u0631\u0628\u064a\u0629'))  # arabic
    print(detect_language('ᜀᜅ᜔ ᜃᜆᜓᜏᜒᜇᜈ᜔ ᜀᜌ᜔ ᜈᜄ᜔ᜉᜉᜇᜃᜒᜎ ᜐ ᜁᜐᜅ᜔ ᜊᜌᜈ᜔'))  # tagalog baybayin
    print(detect_language('तत्सम'))  # hindi
    print(detect_language('௳ ௴ ௵ ௶ ௷ ௸ ௹ ௺'))  # tamil symbols
    print(detect_language('முடி'))  # tamil
    print(detect_language('༖'))  # tibetian
    print(detect_language('\u0627\u064f\u0631\u062f\u064f\u0648\u200e'))  # urdu arabic
    print(detect_language('वह मेरी जान बहाल करता'))  # urdu devanagari
    print(detect_language('Khudáwand merá chaupán hai'))  # urdu roman
