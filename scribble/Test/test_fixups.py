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

import os
from copy import deepcopy
from os.path import dirname
from scribble.fixup import apply_patches


from scribble.model import document


def assert_patch(obj, patch, result):
    obj = deepcopy(obj)
    apply_patches(obj, patch)
    assert result == obj


def test_patches():
    """
    Simple tests of the patch mechanism.
    Note test_object has additional tests which explore longer paths.
    """
    # Boundary case
    assert_patch({}, {}, {})

    # Add a field to an object
    assert_patch({}, {"a": 1}, {"a": 1})
    assert_patch({"a": 1}, {"b": 2, "c": 3}, {"a": 1, "b": 2, "c": 3})

    # Add a new item to an empty array.
    assert_patch([], {"[0]": 1}, [1])
    assert_patch([], {"[+]": 1}, [1])
    assert_patch([], {"[++]": [1]}, [1])

    # Add a new item to a non-empty array
    assert_patch([1], {"[+]": 2}, [1, 2])

    # Replace an existing item
    assert_patch([1], {"[0]": 2}, [2])
    assert_patch({"a": 1}, {"a": 2}, {"a": 2})


def test_document():

    # Process a trivial document.
    #  It invokes both function and and path fixups  (F and P)
    #  for the document instance (I), the document type (T), and a snippet (S).
    #  Each fixup appends two letters to a list which is returned.  eg SF is snippet function.
    output = "/tmp/document.adoc"
    document(
        config=f"{DIR}/testdoc_directory/config/document.yaml",
        directories=[f"{DIR}/testdoc_directory"],
        output=output,
    )

    # Read the output and verify the fixups were inserted correctly.
    with open(output, "r") as f:
        str = f.read()

    # We expect to see functions first, then patches in reverse order. Six total.
    assert str == "TF, TP, IF, IP, SF, SP"

    # clean up
    os.remove(output)


DIR = f"{dirname(__file__)}"
