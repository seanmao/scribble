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

from os import remove
from os.path import dirname

import scribble.config_file as config

DIR = f"{dirname(__file__)}"


def read_write(obj):
    """
    Helper function to write an object out and read it back
    """

    # repeat for each extension type
    for ext in [".json", ".yaml", ""]:

        # Create a temporary file name on a temporary directory.
        #  Note: we actually want an extension on the file name,
        #    even if our test case doesn't use an extension.
        # Also note we are actually creating an empty file.
        #    No problem since we immediately overwrite it.
        real_ext = ext if ext else ".yaml"
        filename = f"/tmp/config_test_file"

        # write out the configuration
        config.write(obj, filename + ext)

        # read it in, specifying the extension
        obj2 = config.read(filename + ext)
        assert obj == obj2

        # read it in, discovering the extension
        obj3 = config.read(filename)
        assert obj == obj2

        # remove the temp file
        remove(filename + real_ext)

        return obj3


def test_basic_values():
    read_write(None)
    read_write(True)
    read_write(False)
    read_write("")
    read_write("abcd")
    read_write(5)
    read_write(0.5)


def test_basic_list():
    # simple list
    read_write([])
    read_write([5])
    read_write([5, 0.5, "Hello"])


def test_basic_dictionary():
    read_write({})
    read_write({"a": 5})
    read_write({"a": 5, "b": 0.5, "c": "Hello"})


def test_nested():
    read_write([[]])
    read_write(["a", ["b"]])
    read_write({"a": {}})
    read_write({"a": {"b": 5}})


def test_mixed():
    read_write([{}])
    read_write({"a": []})
    read_write([{"a": [], "b": {}, "c": [{"d": []}]}])
