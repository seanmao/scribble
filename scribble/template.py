# Copyright 2019 SiFive, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You should have received a copy of LICENSE.Apache2 along with
# this software. If not, you may obtain a copy at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Iterable
from pathlib import Path
import re

from jinja2 import Environment, FileSystemLoader, StrictUndefined, Undefined

from scribble.thirdparty.django import pluralize, yesno


def template(file_name: str, **kwargs: any) -> str:
    """
    Renders a template file to Text.
    :param file_name: template filename.
    :param kwargs: args for the template.
    :return: String rendered from the template.
    """

    # Clean up the file name. Jinja does not like " /../ or ./" in the names.
    # While we're at it, let's verify the file exists.
    file_name = str(Path(file_name).resolve())

    # Load a template from the file.  Note we have to convert path object back to a string.
    templ = _env.get_template(file_name)

    # Render the template, substituting scope plus keywords
    text = templ.render(**kwargs, **GLOBALS)

    # Return the rendered text as a string.
    return (
        text + "\n\n"
    )  # Add blank line so templates don't interfere with following section.


def template_string(template: str, **kwargs: any) -> str:
    """
    Renders a section from a template string.
    :param template:  String containing the template.
    :param kwargs:    Dictionary of template variables (keyword arguments)
    :return:          String rendered from the template.
    """

    # Get a template object from the string
    t = _env.from_string(template)

    # render the template, substituting keywords
    text = t.render(**kwargs, **GLOBALS)

    # return the rendered text as a string.
    return text + "\n\n"  # see above


###################################################
#
# The following routines are used inside templates.
#
###################################################


def _assert(condition: bool, msg: str) -> str:
    """
    Helper function to be used for raising assertion errors in templates.
    """
    if not condition:
        raise AssertionError(msg)
    # Explicitly return '' so that nothing is rendered onto the page.
    return ""


def inline_code(s: str) -> str:
    if not isinstance(s, str):
        raise TypeError("Expected str; got {}".format(type(s)))
    if "`" in s:
        # TODO: Better escaping of ` characters
        raise ValueError("Cannot format text containing backtick (`) as inline code")
    return "``{}``".format(s)


def emphasis(s: str) -> str:
    if not isinstance(s, str):
        raise TypeError("Expected str; got {}".format(type(s)))
    if "__" in s:
        # TODO: Better escaping of ` characters
        raise ValueError(
            "Cannot format text containing double underscore (__) with emphasis"
        )
    return "__{}__".format(s)


def human_size(num):
    """
    Return num as a size in bytes with an appropriate binary prefix (e.g. KiB).

    For numbers that don't divide evenly by a binary prefix (i.e. by a power of
    1024), we format it as a real number with one digit after the decimal
    point (e.g. 2000 bytes == 2.0 KiB).

    >>> human_size(1)
    '1&nbsp;byte'

    >>> human_size(2)
    '2&nbsp;bytes'

    >>> human_size(1024)
    '1&nbsp;KiB'

    >>> human_size(1500)
    '1.5&nbsp;KiB'

    >>> human_size(2048)
    '2&nbsp;KiB'

    >>> human_size(1048576)
    '1&nbsp;MiB'

    >>> human_size(1073741824)
    '1&nbsp;GiB'

    >>> human_size(1099511627776)
    '1&nbsp;TiB'
    """
    if num == 1:
        return "1&nbsp;byte"
    system = [
        (2 ** 40, "&nbsp;TiB"),
        (2 ** 30, "&nbsp;GiB"),
        (2 ** 20, "&nbsp;MiB"),
        (2 ** 10, "&nbsp;KiB"),
        (1, "&nbsp;bytes"),
    ]
    for threshold, suffix in system:
        if num >= threshold:
            if num % threshold == 0:
                return f"{num//threshold}{suffix}"
            else:
                return f"{num/threshold:.1f}{suffix}"
    raise ValueError("Cannot format value less than 1 byte: {num}")


def human_list(items: Iterable[str], serial_comma=True) -> str:
    """Turn a list of strings into a human-readable, English list.

    >>> human_list(['apples', 'bananas', 'oranges'])
    'apples, bananas, and oranges'

    >>> human_list(iter(['apples', 'bananas', 'oranges']))
    'apples, bananas, and oranges'

    >>> human_list(['apples', 'bananas', 'oranges'], serial_comma=False)
    'apples, bananas and oranges'

    >>> human_list(['apples', 'bananas'])
    'apples and bananas'

    >>> human_list(['apple'])
    'apple'

    >>> human_list([])
    Traceback (most recent call last):
        ...
    ValueError: Cannot humanize an empty list
    """
    items = list(items)
    if not items:
        raise ValueError("Cannot humanize an empty list")

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return " and ".join(items)

    but_last = items[:-1]
    last = f"and {items[-1]}"
    if serial_comma:
        return ", ".join(but_last + [last])
    else:
        return "{} {}".format(", ".join(but_last), last)


def hyphenate(phrase: str) -> str:
    """ Translate spaces, dashes and underscores to a non-breaking hyphen. """
    hyphenated = re.sub(r"[_\-\s]+", NON_BREAKING_HYPHEN, phrase)
    return hyphenated


def format_hex(num: int) -> str:
    return f"0x{num:_X}"


def hex_addr(addr: int, pad_bytes: int = 4) -> str:
    num_underscores = (pad_bytes - 1) // 2
    pad_chars = pad_bytes * 2 + num_underscores
    return f"0x{addr:0{pad_chars}_X}"


def wunits(quantity: Any, unit: Any) -> str:
    """Format number with unit and prevent line breaks between them."""
    return f"{quantity}&nbsp;{unit}"


def english_number(num: int) -> str:
    """Return the english-language version of numbers less than 10,
    or the number itself for numbers >= 10. According to
    http://blog.apastyle.org/apastyle/2014/06/comparing-mla-and-apa-numbers.html,
    APA style says to spell out numbers less than 10."""
    english = {
        0: "zero",
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
        7: "seven",
        8: "eight",
        9: "nine",
    }
    return english.get(num, f"{num}")


def _strict_test_none(value: Any) -> bool:
    """
    Stricter version of Jinja's test_none (e.g. {%- if foo is none %}).

    Fails if `value` is a StrictUndefined, catching the case where a variable
    is undefined and not blindly returning True because Undefined is not None.
    """
    if isinstance(value, StrictUndefined):
        value._fail_with_undefined_error()
    return value is None


###################################################
#
# Set up the GLOBALS used for producing templates
#
##################################################
filters = {
    "human_list": human_list,
    "human_size": human_size,
    "inline_code": inline_code,
    "pluralize": pluralize,
    "format_hex": format_hex,
    "hex_addr": hex_addr,
    "english_number": english_number,
    "yesno": yesno,
    "hyphenate": hyphenate,
}


class LooseUndefined(Undefined):
    """
    A version of "Undefined" which is false when used for control,
      but throws exception when printed or iterated. Similar to scribble's INVALID object.
    Being used as an experiment.
    """

    def __str__(self):
        raise Exception(f"Attempting to display an Undefined:")

    def __iter__(self):
        raise Exception(f"Attempting to iterate an Undefined: {self}")

    def __getattr__(self, name):
        return self


_env = Environment(undefined=LooseUndefined, loader=FileSystemLoader("/"))
_env.filters.update(filters)
_env.tests["none"] = _strict_test_none


NON_BREAKING_HYPHEN = "&#8209;"

# Global values available to all templates.
GLOBALS = {
    "assert": _assert,
    "wunits": wunits,
    "len": len,
}
