from language_identification import cld2_wrapper
from language_identification import fasttext_wrapper
from language_identification import langdetect_wrapper
from language_identification import langid_wrapper
from language_identification import nltk_wrapper

LANGUAGE_CODES = {
    'ar': 'Arabic',
    'en': 'English',
    'hi': 'Hindi',
    'id': 'Indonesian',
    'ms': 'Malay',  # not supported by langdetect
    'my': 'Burmese',  # not supported by langid
    'tl': 'Tagalog',
    'ta': 'Tamil',
    'th': 'Thai',
    'vi': 'Vietnamese',
    'zh': 'Chinese',
}

FASTTEXT_LANGUAGES = fasttext_wrapper.SUPPORTED_LANGUAGES
LANGID_LANGUAGES = langid_wrapper.SUPPORTED_LANGUAGES
CLD2_LANGUAGES = cld2_wrapper.SUPPORTED_LANGUAGES

# todo: run tests on fasttext, langid, and cld2-cffi; and use a decent boosting algo to combine the results
# todo: try method proposed
# https://people.eng.unimelb.edu.au/tbaldwin/subjects/socialtext-webst2016/lecture1.pdf (slide 131/218)
# 3-system vote between langid.py, ChromeCLD, and LangDetect is a good choice

# def language_detect(text: str) -> Optional[str]:
#     # cleanup
#     text = clean_text(text)
#
#     # no text input
#     if not text:
#         return None
#
#     # hard-code in this one case
#     if text.lower() == 'assalamualaikum':
#         return 'ms'
#
#     # first, try cld2full (most accurate)
#     try:
#         language_code = langid_cld2full(text)
#         if language_code:
#             return language_code
#     except ValueError:
#         pass
#
#     # second, try cld2 (less accurate)
#     try:
#         language_code = langid_cld2(text)
#         if language_code:
#             return language_code
#     except ValueError:
#         pass
#
#     # use api_call's langid
#     sys_language, sys_score = langid_api_call(text)
#     sys_score *= 0.8  # backend system tends to be overconfident even when wrong
#
#     # last, fallback to langid (constrained to ALWAYS produce an answer)
#     language_code, score = langid_identifier.classify(text)
#
#     if sys_score * 3 / 4 > score:
#         return sys_language
#
#     return language_code

if __name__ == '__main__':
    while True:
        text = input('text:\n')
        print('fasttext:', fasttext_wrapper.detect_language(text, LANGUAGE_CODES.keys()))
        print('langid:', langid_wrapper.detect_language(text, LANGUAGE_CODES.keys()))
        print('langdetect:', langdetect_wrapper.detect_language(text, LANGUAGE_CODES.keys()))
        print('cld2:', cld2_wrapper.detect_language(text, LANGUAGE_CODES.keys()))
        print('cld2full:', cld2_wrapper.detect_language(text, LANGUAGE_CODES.keys(), use_cld2full=True))
        print('nltk:', nltk_wrapper.detect_language(text, LANGUAGE_CODES.keys()))
