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
*   [ ] https://github.com/unicode-org/cldr/blob/master/common/supplemental/supplementalData.xml
    *   [ ] https://unicode-org.github.io/cldr-staging/charts/37/supplemental/languages_and_scripts.html
    *   [ ] https://unicode-org.github.io/cldr-staging/charts/37/supplemental/scripts_and_languages.html
    *   [x] https://en.wikipedia.org/wiki/List_of_ISO_639-2_codes
        *   `mis`, for "uncoded languages";
        *   `mul`, for "multiple languages";
        *   `qaa` - `qtz`, a range reserved for local use.
        *   `und`, for "undetermined";
        *   `zxx`, for "no linguistic content; not applicable";
*   tokenization?
    *   https://www.unicode.org/reports/tr29/#Word_Boundaries



#   TODO
*   [ ] https://en.wiktionary.org/wiki/Category:Basic_word_lists_by_language
*   [ ] use unicode map
    *   [ ] language -> script (+Zyyy)
    *   [ ] script -> chars
    *   [ ] languages (iso 639-2)
    *   [ ] scripts (iso 15924)
*   [ ] pycountry?
    *   [ ] need script alias
*   [ ] how to handle traditional vs simplified chinese
    *   [ ] check the unicode chars?
*   [ ] clean ngrams using proper word tokenizer (ignore numbers)
    *   [ ] ignore any words using wrong scripts
    *   [ ] outliers? loanwords?
*   [ ] get dictionaries for each language


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
*   language code, variation?
    *   eg. "japanese, romaji"
*   script / chars (whitelist)
*   word ngram freqs
    *   char ngram freqs (with start/end chars) (fallback)
    *   n-grams: `[word[i:i + n] for i in range(length - n + 1)]`
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
    *   delete tags `<br>`
*   filter
    *   by script
    *   remove 1-char words
    *   remove common english words
        *   but keep most common vernacular words (whitelist / dictionary)?
*   remove low-count word ngrams
*   count char ngrams


#   cld2
Several embellishments improve the basic algorithm:
*   additional scoring of some sequences of two CJK letters or eight other letters
*   scoring some words and word pairs that are distinctive within sets of statistically-close languages,
    such as {Malay, Indonesian} or {Spanish, Portuguese, Galician}
*   removing repetitive sequences/words that would otherwise skew the scoring,
    such as jpg in foo.jpg bar.jpg baz.jpg
*   removing web-specific words that convey almost no language information,
    such as page, link, click, td, tr, copyright, wikipedia, http.