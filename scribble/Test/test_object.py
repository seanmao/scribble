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

from scribble.obj import subtrees, elevate, split_path, get_path, set_path, scan_leaves
from scribble.objdict import Objdict


def feq(obj, lst):
    flat = list(subtrees(obj))
    assert lst == flat
    assert obj == flat[-1]  # the last entry is the original object


def test_flatten():
    feq({}, [{}])
    feq(5, [5])
    feq([], [[]])
    feq({"a": 15}, [15, {"a": 15}])
    feq([[]], [[], [[]]])

    # Verify dictionary type carries through.
    assert isinstance(list(Objdict().subtrees())[-1], Objdict)


def meq(fn, obj1, obj2):
    m = map(fn, obj1)
    assert obj2 == m


def test_map():
    pass


def eeq(obj1: dict, key: str, obj2: dict):
    e = elevate(obj1, key)
    assert obj2 == e
    assert type(obj2) == type(e)


def test_elevate():
    eeq({}, "", {})
    eeq({"key": {}}, "key", {})
    eeq({"key": {"Howdy": "Doody"}}, "key", {"Howdy": "Doody"})

    # verify dictionary type carries through
    eeq(Objdict(key={}), "key", Objdict())


def equal(obj1, obj2):
    assert obj1 == obj2


# Verify constructs with simple values translate properly
def test_simple():
    equal(Objdict(hello="Hello"), {"hello": "Hello"})
    equal(["abce", 15, 5.3], ["abce", 15, 5.3])
    equal({"hello": "Hello", "nr": 15}, {"hello": "Hello", "nr": 15})


def split(path, lst):
    equal(lst, split_path(path))


# Verify paths can be parsed
def test_path():
    split("a", ["a"])
    split("[5]", ["5"])
    split("", [])
    split("a.b.c[5][6].d.e[4]", ["a", "b", "c", "5", "6", "d", "e", "4"])


# Verify we can extract values based on the path.
def frompath(path, obj, val):
    assert val == get_path(obj, path)


def test_from_path():
    frompath("a", {"a": 5}, 5)
    frompath("[0]", ["a"], "a")
    frompath("a", {}, None)
    frompath("[0]", [], None)  # Treat bad index same as missing field.


# Verify we can insrt values based on path
def topath(path, obj, val):
    set_path(obj, path, val)
    assert val == get_path(obj, path)


def test_to_path():

    # Build up a simple object
    obj = {}
    topath("a", obj, 5)
    topath("b", obj, "Howdy")
    topath("c", obj, {"d": "Doody"})
    frompath("c.d", obj, "Doody")
    topath("e", obj, True)

    # Add a list and verify it can be referenced and updated.
    topath("c.d", obj, ["Howdy", "Doody", "Hello", "World"])
    frompath("c.d[3]", obj, "World")
    topath("c.d[1]", obj, "Hoody")
    topath("c.d[1]", obj, {"theAnswer": 42})
    frompath("c.d[1].theAnswer", obj, 42)


def test_topath_append():
    lst = []
    topath("[0]", lst, 5)
    topath("[1]", lst, 6)
    assert 2 == len(lst)

    # Concatenate a list of values to the end of existing list.
    set_path(lst, "[++]", [7, 8, 9])
    assert 5 == len(lst)
    assert 9 == get_path(lst, "[4]")

    # Add an item
    set_path(lst, "[+]", 10)
    assert 6 == len(lst)
    assert 10 == lst.pop()


def scanleaves(obj, lst):
    assert lst == [value for value, path in scan_leaves(obj)]


def test_scan_leaves():

    # simple types
    scanleaves(5, [5])
    scanleaves("Howdy", ["Howdy"])
    scanleaves(True, [True])

    # simple objects
    scanleaves({"a": 5, "b": 6}, [5, 6])
    scanleaves({"b": 6, "a": 5}, [5, 6])  # sorted by key
    scanleaves([5, 6, 7], [5, 6, 7])

    # nested objects
    scanleaves({"a": 5, "b": {"c": 6}}, [5, 6])
    scanleaves([5, [6]], [5, 6])
    scanleaves({"a": 5, "b": [6, 7]}, [5, 6, 7])
    scanleaves([5, {"b": 6, "c": 7}], [5, 6, 7])

    # verify the path is also correct.
    assert [(5, ".a.b[0]")] == list(scan_leaves({"a": {"b": [5]}}))
    assert [(5, "[0]")] == list(scan_leaves([5]))
    assert [(5, "")] == list(scan_leaves(5))
