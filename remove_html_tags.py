import re
from typing import List

_ALL_HTML_TAGS = [
    # '<!-- -->',  # COMMENTS ARE A SPECIAL CASE

    '<!DOCTYPE>',  # case sensitive only in xml
    '<a>',
    '<abbr>',
    '<address>',
    '<area>',
    '<article>',
    '<aside>',
    '<audio>',
    '<b>',
    '<base>',
    '<bdi>',
    '<bdo>',
    '<blockquote>',
    '<body>',
    '<br>',
    '<button>',
    '<canvas>',
    '<caption>',
    '<cite>',
    '<code>',
    '<col>',
    '<colgroup>',
    '<data>',
    '<datalist>',
    '<dd>',
    '<del>',
    '<details>',
    '<dfn>',
    '<dialog>',
    '<div>',
    '<dl>',
    '<dt>',
    '<em>',
    '<embed>',
    '<fieldset>',
    '<figure>',
    '<footer>',
    '<form>',
    '<h1>',
    '<h2>',
    '<h3>',
    '<h4>',
    '<h5>',
    '<h6>',
    '<head>',
    '<header>',
    '<hgroup>',
    '<hr>',
    '<html>',
    '<i>',
    '<iframe>',
    '<img>',
    '<input>',
    '<ins>',
    '<kbd>',
    '<keygen>',
    '<label>',
    '<legend>',
    '<li>',
    '<link>',
    '<main>',
    '<map>',
    '<mark>',
    '<menu>',
    '<menuitem>',
    '<meta>',
    '<meter>',
    '<nav>',
    '<noscript>',
    '<object>',
    '<ol>',
    '<optgroup>',
    '<option>',
    '<output>',
    '<p>',
    '<param>',
    '<pre>',
    '<progress>',
    '<q>',
    '<rb>',
    '<rp>',
    '<rt>',
    '<rtc>',
    '<ruby>',
    '<s>',
    '<samp>',
    '<script>',
    '<section>',
    '<select>',
    '<small>',
    '<source>',
    '<span>',
    '<strong>',
    '<style>',
    '<sub>',
    '<summary>',
    '<sup>',
    '<table>',
    '<tbody>',
    '<td>',
    '<template>',
    '<textarea>',
    '<tfoot>',
    '<th>',
    '<thead>',
    '<time>',
    '<title>',
    '<tr>',
    '<track>',
    '<u>',
    '<ul>',
    '<var>',
    '<video>',
    '<wbr>',

    # deprecated
    '<acronym>',
    '<applet>',
    '<basefont>',
    '<big>',
    '<blink>',
    '<center>',
    '<dir>',
    '<embed>',
    '<font>',
    '<frame>',
    '<frameset>',
    '<isindex>',
    '<noframes>',
    '<marquee>',
    '<menu>',
    '<plaintext>',
    '<s>',
    '<strike>',
    '<tt>',
    '<u>',
]

# all tag texts, including deprecated tags, compiled into one huge (but fast) regex
_PATTERN_TAG = '(?:(?:!doctype|a(?:bbr|cronym|ddress|pplet|r(?:ea|ticle)|side|udio)?|b(?:ase(?:font)?|d[io]|ig|' \
               'l(?:ink|ockquote)|ody|r|utton)?|c(?:a(?:nvas|ption)|enter|ite|o(?:de|l(?:group)?))|d(?:ata(?:li' \
               'st)?|d|e(?:l|tails)|fn|i(?:alog|r|v)|l|t)|em(?:bed)?|f(?:i(?:eldset|gure)|o(?:nt|oter|rm)|rame(' \
               '?:set)?)|h(?:1|2|3|4|5|6|ead(?:er)?|group|r|tml)|i(?:frame|mg|n(?:put|s)|sindex)?|k(?:bd|eygen)' \
               '|l(?:abel|egend|i(?:nk)?)|m(?:a(?:in|p|r(?:k|quee))|e(?:nu(?:item)?|t(?:a|er)))|n(?:av|o(?:fram' \
               'es|script))|o(?:bject|l|pt(?:group|ion)|utput)|p(?:aram|laintext|r(?:e|ogress))?|q|r(?:b|p|tc?|' \
               'uby)|s(?:amp|cript|e(?:ction|lect)|mall|ource|pan|t(?:r(?:ike|ong)|yle)|u(?:b|mmary|p))?|t(?:ab' \
               'le|body|d|e(?:mplate|xtarea)|foot|h(?:ead)?|i(?:me|tle)|r(?:ack)?|t)|ul?|v(?:ar|ideo)|wbr))'

RE_COMMENT = re.compile(f'(?:<!--(?P<comment>.*)-->)', flags=re.I | re.U)
RE_SCRIPT = re.compile(f'(?:<script(?:\s+[^<>]*)?>.*</script\s*>)', flags=re.I | re.U)
RE_TAG = re.compile(fr'(?:</?{_PATTERN_TAG}(?:\s+[^<>]*)?/?>)', flags=re.I | re.U)


def remove_html_tags(text: str, replacement: str = ' ') -> str:
    text = RE_COMMENT.sub(replacement, text)  # remove all comments first since they could contain half a script
    text = RE_SCRIPT.sub(replacement, text)  # remove entire script, not just the tag
    text = RE_TAG.sub(replacement, text)
    return text


def get_comments(text: str) -> List[str]:
    return [m.group('comment') for m in RE_COMMENT.finditer(text)]
