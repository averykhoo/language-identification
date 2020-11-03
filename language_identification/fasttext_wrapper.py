from pathlib import Path
from typing import Iterable
from typing import List
from typing import Optional

import fasttext
import requests

from language_identification.preprocessing import check_languages
from language_identification.preprocessing import clean_text
from utils import suppress_stdout_stderr

__model_path = Path(__file__).parent / 'lid.176.bin'
__tiny_model_path = Path(__file__).parent / 'lid.176.ftz'


def download_binary_model():
    if not __model_path.exists():
        r = requests.get('https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin')
        with __model_path.open('wb') as f:
            f.write(r.content)


# prefer large binary model
if __model_path.exists():
    with suppress_stdout_stderr():
        fasttext_model = fasttext.load_model(str(__model_path))

# fallback to tiny model
else:
    assert __tiny_model_path.exists()
    with suppress_stdout_stderr():
        fasttext_model = fasttext.load_model(str(__tiny_model_path))

# SUPPORTED_LANGUAGES = ['af', 'als', 'am', 'an', 'ar', ... , 'xmf', 'yi', 'yo', 'yue', 'zh']
SUPPORTED_LANGUAGES: List[str] = sorted(lang.replace('__label__', '') for lang in fasttext_model.get_labels())


def detect_language(text: str, language_codes: Optional[Iterable[str]] = None):
    language_codes = check_languages(language_codes, SUPPORTED_LANGUAGES)

    labels, probabilities = fasttext_model.predict(clean_text(text), k=176)
    labels = [label.replace('__label__', '') for label in labels]
    lang_probs = sorted(zip(labels, probabilities), key=lambda x: x[1], reverse=True)
    return [(lang, prob) for lang, prob in lang_probs if lang in language_codes]
