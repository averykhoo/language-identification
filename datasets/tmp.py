from functools import lru_cache
from typing import Any
from typing import Generator

import unicodedata


@lru_cache(maxsize=0xFFFF)
def is_word_char(char: str) -> bool:
    # todo: special handling for U+00AD (Soft Hyphen)?
    return unicodedata.category(char) in {'Lu', 'Ll', 'Lt', 'Lm', 'Lo',  # letters
                                          # 'Nd', 'Nl', 'No',  # numbers
                                          'Mn', 'Mc', 'Me',  # diacritics, etc
                                          # 'Co',  # private use char class
                                          }


def find_words(text: str) -> Generator[str, Any, None]:
    word_buffer = []
    for char in text:
        # char is part of word
        if is_word_char(char):
            word_buffer.append(char)

        # char is non-text AND buffer is text
        elif word_buffer:
            yield f''.join(word_buffer)
            word_buffer = []

    # yield remainder
    if word_buffer:
        yield f''.join(word_buffer)


def ngrams(seq, n=2):
    return [seq[i:i + n] for i in range(len(seq) - n + 1)]


lang_codes = {
    'Korean':            'kor',
    'ENGLISH':           'eng',
    'POLISH':            'pol',
    'Chinese':           'zho',
    'SPANISH':           'spa',
    'SWEDISH':           'swe',
    'INDONESIAN':        'ind',
    'Japanese':          'jpn',
    'ChineseT':          'zho',
    'ARABIC':            'ara',
    'MALAGASY':          'mlg',
    'FRENCH':            'fra',
    'RUSSIAN':           'rus',
    'BELARUSIAN':        'bel',
    'TAMIL':             'tam',
    'TURKISH':           'tur',
    'DANISH':            'dan',
    'CROATIAN':          'hrv',
    'ITALIAN':           'ita',
    'MACEDONIAN':        'mkd',
    'DUTCH':             'nld',
    'CZECH':             'ces',
    'GREEK':             'ell',
    'GERMAN':            'deu',
    'TELUGU':            'tel',
    'SLOVENIAN':         'slv',
    'FINNISH':           'fin',
    'HUNGARIAN':         'hun',
    'BIHARI':            'bih',
    'PORTUGUESE':        'por',
    'VIETNAMESE':        'vie',
    'MALAYALAM':         'mal',
    'ALBANIAN':          'sqi',
    'MALTESE':           'mlt',
    'Unknown':           None,
    'GALICIAN':          'glg',
    'ESTONIAN':          'est',
    'ARMENIAN':          'hye',
    'NORWEGIAN':         'nor',
    'SERBIAN':           'srp',
    'HEBREW':            'heb',
    'SLOVAK':            'slk',
    'THAI':              'tha',
    'UKRAINIAN':         'ukr',
    'ROMANIAN':          'ron',
    'GEORGIAN':          'kat',
    'LITHUANIAN':        'lit',
    'HINDI':             'hin',
    'BENGALI':           'ben',
    'ICELANDIC':         'isl',
    'LATVIAN':           'lav',
    'PERSIAN':           'fas',
    'SWAHILI':           'swa',
    'TAGALOG':           'tgl',
    'UZBEK':             'uzb',
    'CATALAN':           'cat',
    'BOSNIAN':           'bos',
    'FRISIAN':           'fry',
    'ORIYA':             'ori',
    'SINHALESE':         'sin',
    'MARATHI':           'mar',
    'TURKMEN':           'tuk',
    'AZERBAIJANI':       'aze',
    'BASQUE':            'eus',
    'NORWEGIAN_N':       'nno',
    'BURMESE':           'mya',
    'BULGARIAN':         'bul',
    'TIGRINYA':          'tir',
    'SOMALI':            'som',
    'LUXEMBOURGISH':     'ltz',
    'MALAY':             'msa',
    'URDU':              'urd',
    'GUJARATI':          'guj',
    'KAZAKH':            'kaz',
    'TAJIK':             'tgk',
    'KANNADA':           'kan',
    'HAUSA':             'hau',
    'DHIVEHI':           'div',
    'PASHTO':            'pus',
    'MONGOLIAN':         'mon',
    'KURDISH':           'kur',
    'PUNJABI':           'pan',
    'KINYARWANDA':       'kin',
    'WELSH':             'cym',
    'RHAETO_ROMANCE':    'roa',
    'AYMARA':            'aym',
    'WARAY_PHILIPPINES': 'war',
    'OROMO':             'orm',
    'KYRGYZ':            'kir',
    'IRISH':             'gle',
    'SCOTS_GAELIC':      'gla',
    'GANDA':             'lug',
    'AFRIKAANS':         'afr',
    'FAROESE':           'fao',
    'YORUBA':            'yor',
    'NYANJA':            'nya',
    'AMHARIC':           'amh',
    'LATIN':             'lat',  # no useful data
    'CORSICAN':          'cos',
    'IGBO':              'ibo',
    'SESELWA':           None,  # iso 639-3 -> 'crs'
    'SAMOAN':            'smo',
    'LINGALA':           'lin',
    'XHOSA':             'xho',
    'TIBETAN':           'bod',
    'OCCITAN':           'oci',  # no useful data
    'NEPALI':            'nep',
    'GUARANI':           'grn',
    'HMONG':             'hmn',  # no useful data
    'TATAR':             'tat',  # no useful data
}
