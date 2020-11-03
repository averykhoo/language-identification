from typing import Iterable
from typing import Optional

from nltk.classify import textcat

from language_identification.iso639_3 import iso639_3_2
from language_identification.preprocessing import check_languages
from language_identification.preprocessing import clean_text

textcat_model = textcat.TextCat()
SUPPORTED_LANGUAGES = sorted(iso639_3_2.get(lang, lang) for lang in
                             ['abk', 'abn', 'ace', 'ach', 'acu', 'ada', 'afr', 'agr', 'aja', 'aka',
                              'ako', 'alt', 'amc', 'ame', 'amh', 'ami', 'amr', 'arg', 'ang', 'arb',
                              'arl', 'arn', 'asm', 'ast', 'ava', 'ayr', 'azj', 'bak', 'bcc', 'ban',
                              'bar', 'bas', 'bba', 'bci', 'bel', 'bem', 'bfa', 'bul', 'bho', 'bis',
                              'bcl', 'bin', 'bam', 'ben', 'boa', 'bod', 'bre', 'bos', 'btb', 'bxr',
                              'buc', 'bug', 'bum', 'byv', 'cab', 'cat', 'cak', 'cbr', 'cbs', 'cbt',
                              'cbu', 'ceb', 'cha', 'chj', 'chk', 'chw', 'cic', 'cjk', 'cnh', 'cni',
                              'cos', 'cop', 'cot', 'cpu', 'crk', 'crs', 'csa', 'csb', 'ces', 'chu',
                              'cuk', 'chv', 'cym', 'czt', 'dan', 'dag', 'dar', 'ddn', 'deu', 'dga',
                              'dhv', 'diq', 'dsb', 'dua', 'dyo', 'dyu', 'dzo', 'ewe', 'efi', 'ell',
                              'emk', 'eml', 'eng', 'eng ', 'epo', 'spa', 'est', 'eus', 'pes', 'fub',
                              'fin', 'fij', 'fao', 'fon', 'fra', 'frr', 'frp', 'fud', 'fuf', 'fur',
                              'fri', 'gaa', 'gle', 'gag', 'gya', 'gla', 'gil', 'gjn', 'gkn', 'glg',
                              'gug', 'got', 'gsc', 'gsw', 'guc', 'guj', 'guw', 'glv', 'gym', 'hau',
                              'haw', 'heb', 'hin', 'hil', 'hna', 'hne', 'hni', 'hmo', 'hrv', 'hsb',
                              'hat', 'hun', 'huu', 'hve', 'hye', 'her', 'ina', 'iba', 'ind', 'ibo',
                              'igl', 'ilo', 'inh', 'isl', 'iso', 'ita', 'its', 'ike', 'ivv', 'jiv',
                              'jav', 'kab', 'kac', 'kat', 'kam', 'kbd', 'kbp', 'kcc', 'kck', 'kde',
                              'kek', 'kng', 'kha', 'kik', 'kua', 'kjh', 'kaz', 'kal', 'kmb', 'khm',
                              'kan', 'knn', 'koo', 'kos', 'gkp', 'kqn', 'krc', 'knc', 'kri', 'ksh',
                              'ktu', 'kmr', 'kum', 'kpv', 'kwf', 'cor', 'kwn', 'kir', 'lad', 'lat',
                              'lbe', 'ltz', 'lch', 'lug', 'lgg', 'lia', 'nld', 'lij', 'lld', 'lmo',
                              'lms', 'lnc', 'lin', 'lns', 'lao', 'lol', 'loz', 'lit', 'lua', 'lue',
                              'lub', 'lun', 'luo', 'lus', 'lav', 'mad', 'mam', 'mau', 'maz', 'mcd',
                              'mcf', 'mdf', 'men', 'meu', 'mfe', 'plt', 'mah', 'mhi', 'mho', 'mic',
                              'mri', 'min', 'miq', 'mir', 'mkd', 'mal', 'mlu', 'khk', 'ron', 'mos',
                              'mar', 'mrj', 'mly', 'mlt', 'mua', 'mus', 'mwv', 'mxv', 'mya', 'myv',
                              'mzn', 'nau', 'nhe', 'nap', 'naq', 'nba', 'nob', 'ndc', 'nde', 'nds',
                              'nep', 'nen', 'ndo', 'ngl', 'nia', 'niu', 'nmf', 'nnb', 'nno', 'not',
                              'nbl', 'nso', 'nav', 'nya', 'nyk', 'nym', 'nyn', 'nzi', 'ogo', 'ojw',
                              'gaz', 'ood', 'ori', 'oss', 'pan', 'pag', 'pam', 'pap', 'pau', 'pbb',
                              'pcm', 'pdc', 'pem', 'pih', 'pis', 'pol', 'pms', 'pon', 'ppl', 'prq',
                              'prs', 'prv', 'pbu', 'por', 'quh', 'qug', 'rar', 'rcf', 'roh', 'rnd',
                              'run', 'rmn', 'rus', 'rug', 'rup', 'kin', 'sba', 'src', 'scn', 'sco',
                              'snd', 'sme', 'seh', 'sag', 'shp', 'shs', 'sid', 'slk', 'slv', 'smo',
                              'sna', 'snk', 'som', 'ses', 'sop', 'als', 'srp', 'srm', 'srn', 'srr',
                              'ssw', 'sot', 'sun', 'suk', 'sum', 'sus', 'swe', 'swb', 'swh', 'tab',
                              'tam', 'tbz', 'tel', 'tem', 'teo', 'tet', 'tgk', 'tha', 'tir', 'tig',
                              'tiv', 'tuk', 'tkl', 'tgl', 'tll', 'tsn', 'tob', 'ton', 'toi', 'toj',
                              'tos', 'tpi', 'tur', 'tsc', 'tso', 'tat', 'ttj', 'tum', 'tvl', 'tah',
                              'tzc', 'tzm', 'udm', 'uig', 'ukr', 'umb', 'ura', 'urd', 'urh', 'uzn',
                              'vec', 'ven', 'vie', 'vls', 'vmf', 'vmw', 'wal', 'war', 'wls', 'wol',
                              'xal', 'xho', 'xsm', 'yad', 'yaf', 'yao', 'yap', 'ydd', 'yor', 'yua',
                              'ccx', 'zai', 'zea', 'cmn', 'zne', 'zpa', 'zul'])


def detect_language(text: str, language_codes: Optional[Iterable[str]] = None):
    language_codes = check_languages(language_codes, SUPPORTED_LANGUAGES)

    results = [(lang, 1 / dist) for lang, dist in textcat_model.lang_dists(clean_text(text)).items()]
    results = [(iso639_3_2[lang], prob) for lang, prob in results if lang in iso639_3_2]
    normalize_constant = sum(prob for lang, prob in results)
    results = [(lang, prob / normalize_constant) for lang, prob in results]
    results = sorted(results, key=lambda x: x[1], reverse=True)
    return [(lang, prob) for lang, prob in results if lang in language_codes]
