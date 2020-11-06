#   language identification
testing repo


##  N-gram dataset
*   http://data.gdeltproject.org/gdeltv3/web/ngrams/LASTUPDATE.TXT
*   http://data.gdeltproject.org/gdeltv3/web/ngrams/MASTERFILELIST.TXT
*   http://data.gdeltproject.org/blog/2019-gfg-august-2019-ngrams/MASTER.LINGUISTIC.1GRAM.TXT.gz
*   http://data.gdeltproject.org/blog/2019-gfg-august-2019-ngrams/MASTER.LINGUISTIC.2GRAM.TXT.gz
*   http://data.gdeltproject.org/gdeltv3/geg_gcnlapi/MASTERFILELIST.TXT
*   http://data.gdeltproject.org/gdeltv3/gfg/alpha/lastupdate.txt

### Languages in dataset are:
*   AFRIKAANS
*   ALBANIAN
*   AMHARIC
*   ARABIC
*   ARMENIAN
*   AYMARA
*   AZERBAIJANI
*   BASQUE
*   BELARUSIAN
*   BENGALI
*   BIHARI
*   BOSNIAN
*   BULGARIAN
*   BURMESE
*   CATALAN
*   CORSICAN
*   CROATIAN
*   CZECH
*   Chinese
*   ChineseT
*   DANISH
*   DHIVEHI
*   DUTCH
*   ENGLISH
*   ESTONIAN
*   FAROESE
*   FINNISH
*   FRENCH
*   FRISIAN
*   GALICIAN
*   GANDA
*   GEORGIAN
*   GERMAN
*   GREEK
*   GUARANI
*   GUJARATI
*   HAUSA
*   HEBREW
*   HINDI
*   HMONG
*   HUNGARIAN
*   ICELANDIC
*   IGBO
*   INDONESIAN
*   IRISH
*   ITALIAN
*   Japanese
*   KANNADA
*   KAZAKH
*   KINYARWANDA
*   KURDISH
*   KYRGYZ
*   Korean
*   LATIN
*   LATVIAN
*   LINGALA
*   LITHUANIAN
*   LUXEMBOURGISH
*   MACEDONIAN
*   MALAGASY
*   MALAY
*   MALAYALAM
*   MALTESE
*   MARATHI
*   MONGOLIAN
*   NEPALI
*   NORWEGIAN
*   NORWEGIAN_N
*   NYANJA
*   OCCITAN
*   ORIYA
*   OROMO
*   PASHTO
*   PERSIAN
*   POLISH
*   PORTUGUESE
*   PUNJABI
*   RHAETO_ROMANCE
*   ROMANIAN
*   RUSSIAN
*   SAMOAN
*   SCOTS_GAELIC
*   SERBIAN
*   SESELWA
*   SINHALESE
*   SLOVAK
*   SLOVENIAN
*   SOMALI
*   SPANISH
*   SWAHILI
*   SWEDISH
*   TAGALOG
*   TAJIK
*   TAMIL
*   TATAR
*   TELUGU
*   THAI
*   TIBETAN
*   TIGRINYA
*   TURKISH
*   TURKMEN
*   UKRAINIAN
*   URDU
*   UZBEK
*   Unknown
*   VIETNAMESE
*   WARAY_PHILIPPINES
*   WELSH
*   XHOSA
*   YORUBA

##  links
*   [how Aspell works](http://aspell.net/0.50-doc/man-html/8_How.html)
*   [symspell](https://github.com/wolfgarbe/SymSpell#blog-posts-algorithm-benchmarks-applications)
*   [An Overview of Fuzzy Name Matching Techniques](https://www.rosette.com/blog/overview-fuzzy-name-matching-techniques)
*   [Zipf's law](https://en.wikipedia.org/wiki/Zipf's_law)
    *   https://core.ac.uk/download/pdf/22877794.pdf
    *   https://www.aclweb.org/anthology/W96-0106.pdf
    *   https://arxiv.org/pdf/cmp-lg/9606013.pdf
    *   https://www.degruyter.com/view/journals/cllt/14/1/article-p1.xml?language=en
    *   https://statweb.stanford.edu/~owen/courses/306a/ZipfAndGutenberg.pdf
    *   https://besjournals.onlinelibrary.wiley.com/doi/full/10.1111/2041-210X.12768
    

## Unicode
*   https://www.unicode.org/Public/UCD/latest/ucdxml/ucd.all.flat.zip
*   https://en.wikipedia.org/wiki/ISO_15924
    *   https://unicode.org/iso15924/iso15924-num.html
    *   https://unicode.org/iso15924/iso15924.txt.zip
*   https://en.wikipedia.org/wiki/International_uniformity_of_braille_alphabets
*   https://en.wikipedia.org/wiki/Tengwar
*   https://github.com/unicode-org/cldr/blob/master/common/supplemental/supplementalData.xml
    *   https://unicode-org.github.io/cldr-staging/charts/37/supplemental/languages_and_scripts.html
    *   https://unicode-org.github.io/cldr-staging/charts/37/supplemental/scripts_and_languages.html
    *   https://en.wikipedia.org/wiki/List_of_ISO_639-2_codes
*   tokenization?
    *   https://www.unicode.org/reports/tr29/#Word_Boundaries
    *   special handling for U+00AD (Soft Hyphen)?
```python
import unicodedata
from typing import Callable, Generator, Any

def memoize(f: Callable) -> Callable:
    """
    memoization decorator for a function taking ONLY a single argument
    src: http://code.activestate.com/recipes/578231-probably-the-fastest-memoization-decorator-in-the-/
    """

    class MemoDict(dict):
        def __missing__(self, key):
            ret = self[key] = f(key)
            return ret

    return MemoDict().__getitem__

@memoize
def is_word_char(char: str) -> bool:
    return unicodedata.category(char) in {'Lu', 'Ll', 'Lt', 'Lm', 'Lo',  # letters
                                          # 'Nd', 'Nl', 'No',  # numbers
                                          'Mn', 'Mc', 'Me',  # diacritics, etc
                                          # 'Co',  # private use char class
                                          }

def words(text: str) -> Generator[str, Any, None]:
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
```



#   TODO
-   use unicode map
    -   language -> script
    -   script -> chars
    -   languages (iso 639-2)
    -   scripts (iso 15924)
-   how to handle traditional vs simplified chinese
    -   check the unicode chars?
-   clean ngrams using proper word tokenizer (ignore numbers)
    -   ignore any words using wrong scripts
    -   outliers? loanwords?
-   get dictionaries for each language
