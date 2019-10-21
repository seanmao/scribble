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

from scribble.exceptions import DocumentException
from scribble.objdict import Objdict, INVALID


def equal(obj1, obj2):
    assert Objdict.from_obj(obj1) == obj2


# a universal class which has attributes passed in.
class id:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# Verify primitive values are left unchanged
def test_primitives():
    equal(15, 15)
    equal(True, True)
    equal("Howdy", "Howdy")
    equal(5.3, 5.3)


# Verify empty constructs
def xxxtest_empty():
    equal([], [])
    equal({}, {})
    equal(id(), {})


# Verify constructs with simple values translate properly
def test_simple():
    equal(id(hello="Hello"), {"hello": "Hello"})
    equal(["abce", 15, 5.3], ["abce", 15, 5.3])
    equal({"hello": "Hello", "nr": 15}, {"hello": "Hello", "nr": 15})


# Verify nested constructs translate
listOfThings = [["abcd"], {"hello": "Hello"}, id(foo="bar")]
dictOfThings = {"a": ["abcd"], "b": {"hello": "Hello"}, "c": id(foo="bar")}
objOfThings = id(a=["abcd"], b={"hello": "Hello"}, c=id(foo="bar"))


def test_nested():
    equal(listOfThings, [["abcd"], {"hello": "Hello"}, {"foo": "bar"}])
    equal(dictOfThings, {"a": ["abcd"], "b": {"hello": "Hello"}, "c": {"foo": "bar"}})
    equal(objOfThings, {"a": ["abcd"], "b": {"hello": "Hello"}, "c": {"foo": "bar"}})
    assert Objdict.from_obj(dictOfThings) == Objdict.from_obj(objOfThings)


# Verify we can access fields as dictionary or as object.
def test_references():

    list = Objdict.from_obj(listOfThings)
    assert list[1].hello == list[1]["hello"]
    assert list[0][0] == "abcd"

    obj = Objdict.from_obj(objOfThings)
    assert obj.b.hello == obj["b"]["hello"]
    assert obj.a[0] == "abcd"
    assert obj["a"][0] == "abcd"


def test_NoDict():

    # INVALID is falsish
    assert not INVALID

    # INVALID can be referenced as list, object or dict and returns INVALID
    assert INVALID.x is INVALID
    assert INVALID[5] is INVALID
    assert INVALID["key"] is INVALID

    # A non-existent Objdict reference becomes INVALID
    assert Objdict().x is INVALID
    assert Objdict()[5] is INVALID

    # INVALID throws exception when formatted.
    try:
        f"{INVALID}"
        assert False
    except DocumentException:
        assert True

    # INVALID only equals None or INVALID
    assert INVALID == INVALID
    assert INVALID == None  # noqa: E711 allow comparison to None
    assert None == INVALID  # noqa: E711 allow comparison to None
    assert not INVALID == 0
    assert not INVALID == {}
    assert not INVALID == []

    # INVALID is an empty iterator
    for x in INVALID:
        assert False, "INVALID should be empty and not iterate"


# Verify we can initialize, reference and delete values
def test_Objdict():

    # an empty object tests as False
    assert not Objdict()

    obj = Objdict(value=10)
    assert "value" in obj
    assert obj.value == 10

    assert obj.other is INVALID
    del obj["value"]
    assert "value" not in obj
    assert obj.value is INVALID

    obj["value"] = 20
    assert obj.value == 20
    obj.value = None
    assert "value" not in obj

    obj.value = 30
    assert obj["value"] == 30
    obj["value"] = None  # Problem - assigns None
    assert "value" in obj  # TODO: How can we capture this assignment?
    delattr(obj, "value")
    assert "value" not in obj

    assert obj.get("value", 40) == 40
    obj.value = 50
    assert obj.get("value", 40) == 50


# Test the "path" functions (which are used for querying units)
def test_path():
    obj = Objdict()
    obj.set_path("howdy.doody", 10)
    assert obj.howdy.doody == 10
    assert obj.get_path("howdy.doody") == 10

    assert obj.get_path("") is obj
    assert obj.get_path("howdy") == {"doody": 10}
    assert obj.get_path("howdy.partner") is None
