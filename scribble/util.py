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

from typing import List
from scribble.exceptions import DocumentException
from scribble.scope import Element
from scribble.section import Text


def consistent_values(elements: List[Element], *paths: str):
    """
    Verifies all the elements have equal data items. Throws exception on failure.
       We are checking for consistent values, NOT for invalid data.
       It is OK if the value is missing, as long as it is missing on all of the elements.
    :param elements: A List of similar elements
    :param paths: the reference paths which must match
    """
    # if there is more than one element
    if len(elements) > 1:

        # For each of the given paths
        for path in paths:

            # Compare the first element with all the subsequent ones
            first = elements[0].get_path(path)
            for subsequent in elements[1:]:
                current = subsequent.get_path(path)

                # Raise an exception if they have different values.
                if first != current:
                    raise DocumentException(
                        f"Inconsistent values: {path} -- {first}|{current}"
                    )


def plus1() -> Text:
    return Text("\n\n:leveloffset: +1\n\n")


def minus1() -> Text:
    return Text("\n\n:leveloffset: -1\n\n")


def n_bytes(x: int) -> int:
    """
    number of bytes to hold the given value.
    """
    assert x >= 0

    # Get number of bits and bytes.
    bits = x.bit_length()  # 1 or greater.
    bytes = (bits + 7) >> 3  # 1 or greater.
    return bytes


def log2up(n: int) -> int:
    """
    Returns log2 of a number, rounded up.
    """
    return (n - 1).bit_length()
