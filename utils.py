import os
import re
from typing import Iterable
from typing import Optional
from typing import Tuple
from typing import Union

import ftfy
# noinspection PyProtectedMember
from bs4 import UnicodeDammit

RE_WHITESPACE = re.compile(r'\s', flags=re.U)


def ensure_unicode(text: str,
                   most_likely_encodings: Union[str, Iterable[str]] = (),
                   ) -> str:
    if isinstance(most_likely_encodings, str):
        most_likely_encodings = [most_likely_encodings]
    elif isinstance(most_likely_encodings, Iterable):
        most_likely_encodings = list(most_likely_encodings)
    else:
        raise TypeError(most_likely_encodings)

    # decode bytes
    if isinstance(text, (bytes, bytearray)):
        text = UnicodeDammit.detwingle(text)

    # unexpected type, just coerce
    elif not isinstance(text, str):
        text = str(text)

    # convert to unicode
    text = UnicodeDammit(text, most_likely_encodings).unicode_markup

    # ftfy for good measure
    return ftfy.fix_text(text)


UPLOADED_FILE_INFO_HEADERS = ['path',
                              'filename',
                              'extension',
                              'size',
                              'sha256',
                              'md5',
                              'created',
                              ]


def split_filename(filename: Union[os.PathLike, str]) -> Tuple[str, str]:
    extension_max_len = 6  # arbitrary, but must fit '.docx'

    # split into filename and extension
    filename, extension = ensure_unicode(os.path.basename(filename)).rsplit('.', 1)
    extension = '.' + extension.strip().lower()

    # suffixes to allow
    _suffixes = {
        '.gz',
        '.bz2',
        '.lz',
        '.lzma',
        '.lzo',
        '.xz',
        '.z',
        '.zst',
    }
    _suffixes.update([f'.{i:03d}' for i in range(100)])  # .001, .002, ..., .099

    # special handling for known suffix
    extension_suffix = ''
    if extension in _suffixes and '.' in filename[-extension_max_len:]:
        extension_suffix = extension
        filename, extension = filename.rsplit('.', 1)
        extension = '.' + extension.strip().lower()

    # fix extensions
    if len(extension) > extension_max_len:
        filename, extension = filename + extension, ''
    elif extension == '.htm':  # normalize to html
        extension = '.html'
    elif extension == '.jpeg':  # normalize to jpg
        extension = '.jpg'

    # replace extension suffix
    extension += extension_suffix

    return filename.strip(), extension


def truncate_text(text: str,
                  max_bytes_length: Optional[int] = None,
                  max_str_length: Optional[int] = None,
                  truncate_to_space: bool = True,
                  ) -> str:
    # no text input
    if not text:
        return ''

    if max_str_length is not None:
        truncated_str_length = min(max_str_length, len(text))
    else:
        truncated_str_length = len(text)

    if max_bytes_length is not None:
        # impose length limit on ENCODED text
        truncated_str_length = min(max_bytes_length, truncated_str_length)
        min_length = 0
        while len(text[:truncated_str_length].encode('utf8')) > max_bytes_length:
            delta_length = (truncated_str_length - min_length) // 2
            if delta_length == 0:
                truncated_str_length -= 1
                break

            # bisect the length until we find the right spot
            if len(text[:min_length + delta_length].encode('utf8')) > max_bytes_length:
                truncated_str_length = min_length + delta_length
            else:
                min_length = min_length + delta_length

    # if text has to be truncated, keep going back until we see whitespace (search the last 1% of the text)
    if truncate_to_space and truncated_str_length < len(text):
        for i in range(truncated_str_length // 100):
            if RE_WHITESPACE.fullmatch(text[truncated_str_length - i]) is not None:
                text = text[:truncated_str_length - i]
                break

        # no whitespace found, just truncate
        else:
            text = text[:truncated_str_length]

    return text.strip()


class suppress_stdout_stderr(object):
    """
    A context manager for doing a "deep suppression" of stdout and stderr in
    Python, i.e. will suppress all print, even if the print originates in a
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).

    """

    def __init__(self):
        # Open a pair of null files
        self.null_fds = [os.open(os.devnull, os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = [os.dup(1), os.dup(2)]

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0], 1)
        os.dup2(self.null_fds[1], 2)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0], 1)
        os.dup2(self.save_fds[1], 2)
        # Close all file descriptors
        for fd in self.null_fds + self.save_fds:
            os.close(fd)
