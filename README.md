#   language identification
testing repo


##  [x] N-gram dataset
*   http://data.gdeltproject.org/gdeltv3/web/ngrams/LASTUPDATE.TXT
*   http://data.gdeltproject.org/gdeltv3/web/ngrams/MASTERFILELIST.TXT
*   http://data.gdeltproject.org/blog/2019-gfg-august-2019-ngrams/MASTER.LINGUISTIC.1GRAM.TXT.gz
*   http://data.gdeltproject.org/blog/2019-gfg-august-2019-ngrams/MASTER.LINGUISTIC.2GRAM.TXT.gz
*   http://data.gdeltproject.org/gdeltv3/geg_gcnlapi/MASTERFILELIST.TXT
*   http://data.gdeltproject.org/gdeltv3/gfg/alpha/lastupdate.txt


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
*   [x] https://www.unicode.org/Public/UCD/latest/ucdxml/ucd.all.flat.zip
*   [x] https://en.wikipedia.org/wiki/ISO_15924
    *   [ ] ~~https://unicode.org/iso15924/iso15924-num.html~~
    *   [x] https://unicode.org/iso15924/iso15924.txt.zip
*   [ ] https://en.wikipedia.org/wiki/International_uniformity_of_braille_alphabets
*   [ ] https://en.wikipedia.org/wiki/Tengwar
*   [x] https://github.com/unicode-org/cldr/blob/master/common/supplemental/supplementalData.xml
    *   [x] https://unicode-org.github.io/cldr-staging/charts/37/supplemental/languages_and_scripts.html
    *   [x] https://unicode-org.github.io/cldr-staging/charts/37/supplemental/scripts_and_languages.html
    *   [x] https://en.wikipedia.org/wiki/List_of_ISO_639-2_codes
        *   `mis`, for "uncoded languages";
        *   `mul`, for "multiple languages";
        *   `qaa` - `qtz`, a range reserved for local use.
        *   `und`, for "undetermined";
        *   `zxx`, for "no linguistic content; not applicable";
*   tokenization?
    *   https://www.unicode.org/reports/tr29/#Word_Boundaries
*   NKFD decompose before match?
    *   allow dropping of M* chars for match?



#   TODO
*   [ ] ~~https://en.wiktionary.org/wiki/Category:Basic_word_lists_by_language~~
*   [x] use unicode map
    *   [x] language -> script (+Zyyy)
    *   [x] script -> chars
    *   [x] languages (iso 639-2)
    *   [x] scripts (iso 15924)
*   [ ] pycountry?
    *   [ ] need script alias
*   [x] how to handle traditional vs simplified chinese
    *   [x] check the unicode chars?
*   [x] clean ngrams using proper word tokenizer (ignore numbers)
    *   [ ] ignore any words using wrong scripts
    *   [ ] outliers? loanwords?
        *   common english words
        *   common multilingual words
*   [x] get dictionaries for each language
    *   [x] dump dictionaries from some free apks
    *   [ ] parse dictionaries
*   [ ] rebuild models from clean corpora
    *   dictionaries
        *   [ ] [GNOME](http://opus.nlpl.eu/GNOME.php) / [KDE4](http://opus.nlpl.eu/KDE4.php) / [Ubuntu](http://opus.nlpl.eu/Ubuntu.php)
        *   [ ] [tatoeba](http://opus.nlpl.eu/Tatoeba.php)
        *   [ ] [unimorph](https://unimorph.github.io/)
        *   [ ] [memolon](https://github.com/JULIELab/MEmoLon/tree/master/memolon/data/TranslationTables)
        *   [ ] stopwords corpus
    *   word / char ngrams
        *   [ ] [UDHR](https://www.kaggle.com/nltkdata/udhr-corpus) [Alt](http://research.ics.aalto.fi/cog/data/udhr/)
        *   [ ] [JW300](http://opus.nlpl.eu/JW300.php)
        *   [ ] [bible](http://opus.nlpl.eu/bible-uedin.php)
        *   [ ] [W2C](http://ufal.mff.cuni.cz/~majlis/w2c/download.html)
    
*   other corpora
    *   [ELG catalog](https://live.european-language-grid.eu/catalogue/#/)


#   script lookup
*   ~~binary tree?~~
*   ~~based on ip-lookup? (ranges in sets)~~
    *   ~~unicode max is 0x10FFFF~~
    *   ~~masks:~~
        *   ~~0xfffff0~~
        *   ~~0xffffe0~~
        *   ~~0xffffc0~~
        *   ~~0xffff80~~
        *   ~~0xffff00~~
        *   ~~0xfffe00~~
        *   ~~0xfffc00~~
        *   ~~0xfff800 <- max 544 of these~~
*   just use one set per lang / script and use lrucache(maxsize=0xFFFF)
*   char -> langs or char -> scripts?

#   modular langid
*   language code, variation/dialect name
    *   eg. "japanese, romaji" or "english, deseret"
*   script / charset (whitelist)
*   (optional) word ngram freqs
    *   1-gram at a minimum
    *   char ngram freqs (with start/end chars) (fallback)
    *   n-grams: `[word[i:i + n] for i in range(length - n + 1)]`
    *   if no words, just use ngrams
*   (optional) char ngram freqs
    *   chars only, no spaces etc
        *   clean on load? or error?
        *   use the script as whitelist?
    *   if no chars, build from word freqs
    *   if no chars and no words, assume uniform distribution over all chars, but L* gets priority over M*
    *   some kind of smoothing where you specify the total population of ngrams
*   kenlm?
    *   (decoder only) `pip install https://github.com/kpu/kenlm/archive/master.zip`
    *   [example.py](https://github.com/kpu/kenlm/blob/master/python/example.py)
*   nltk?
    *   [kneser ney](https://www.nltk.org/api/nltk.lm.html#nltk.lm.models.KneserNeyInterpolated)


#   cleanup
*   mimic cld2 cleanup
    *   expand HTML entities `&amp;` 
    *   delete digits
    *   delete punctuation
    *   delete all html tags `<br>`
    *   removing repetitive sequences/words that would otherwise skew the scoring,
        such as jpg in foo.jpg bar.jpg baz.jpg
    *   removing web-specific words that convey almost no language information,
        such as page, link, click, td, tr, copyright, wikipedia, http.
*   more cleanup
    *   emails, urls, twitter handles, hashtags
    *   common tech terms (pdf, jpg, ppt, docx, htm, href)
    *   common entities (facebook, instagram, chrome, twitter, wiki)
*   filter
    *   by script
    *   remove 1-char words
    *   remove common english words
        *   but keep most common vernacular words (whitelist / dictionary)?
*   remove low-count word ngrams
*   count char ngrams
*   dedupe repeated chars?
    *   hello -> helo <- hellloooo
    *   `1608.03030` -> sequences such as 'hahahaha...' or 'arghhhhh...' 
                        we restricted any sequence of repeating characters to at most five repetitions
                        where the repeating pattern can be from one to four characters


#   cld2
Several embellishments improve the basic algorithm:
*   additional scoring of some sequences of two CJK letters or eight other letters
*   scoring some words and word pairs that are distinctive within sets of statistically-close languages,
    such as {Malay, Indonesian} or {Spanish, Portuguese, Galician}