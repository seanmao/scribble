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

from __future__ import annotations

import re
from collections import OrderedDict
from typing import Any, Iterator, List, Iterable, TypeVar

T = TypeVar("T")


def subtrees(obj: Any) -> Iterator[Any]:
    """
    Scan through all elements of an object structure, yielding a sequence of subtrees.
    :param obj: object to be scanned
    :return: iteration of subobjects
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from subtrees(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from subtrees(v)
    else:
        pass

    yield obj


def scan(obj: Any, fn):
    """
    Pre-order scan all subobjects of an object, invoking a function at each subobject.
    Unlike subtrees() above, the object can be mutated as it is scanned.
    """
    if isinstance(obj, dict):
        fn(obj)
        for k, v in obj.items():
            scan(v, fn)

    elif isinstance(obj, list):
        for v in obj:
            scan(v, fn)

    else:
        pass


def get_path(obj: dict, key: str) -> Any:
    """
    Fetches a value given a key, where the key is a dot separated path.
        Allows shortcut:   getPath(obj, "a.b.c")   -->   obj["a"]["b"["c"]
        but returns None if the intermediate values are not defined.
    """
    # Split the path into pieces
    path = split_path(key)

    # Scan down the path, one piece at a time, stopping if None (not defined)
    val = obj
    for p in path:
        if isinstance(val, list) and 0 <= int(p) < len(val):
            val = val[int(p)]
        elif isinstance(val, dict) and p in val:
            val = val[p]
        else:
            return None
    return val


def set_path(obj: dict, key: str, value: Any):
    """
    Set a value for the given key, where the key is a dot separated path.
        Allows shortcut:   setPath(obj, "a.b.c", value)   -->   obj["a"]["b"["c"] = value
        but it creates intermediate nodes if they don't already exist.
    """
    # Split the path into pieces
    path = split_path(key)
    last = path.pop()

    # Scan down the path, one piece at a timem, creating empty maps as needed.
    #  Assumes intermediate objects are lists or dicts.
    val = obj
    for p in path:
        # Case: Index into existing list
        if isinstance(val, list):  # Index into existing list.
            val = val[int(p)]
        # Case: Follow existing key.
        elif p in val:
            val = val[p]
        # Case: Create new empty list.
        elif p == "0" or p == "+" or p == "++":
            val = []
        # Case: Create new dictionary with entry.
        else:
            val[p] = type(val)()
            val = val[p]

    # save the value in the final position.

    # CASE List:
    if isinstance(val, list):
        # CASE: "++",  append new list to existing list.
        if last == "++":
            val = val.extend(value)

        # CASE: end of list or "+", add new value to end of list
        elif last == "+" or int(last) == len(val):
            val.append(value)

        # OTHERWISE, insert new value into array. (throw exception if out of bounds)
        else:
            val[int(last)] = value

    # Case: Map:  Save the new value.
    else:
        val[last] = value


def split_path(path: str) -> List[str]:
    pieces = re.findall(splitter, path)
    return pieces


splitter = r"[\w\+]+"  # Find  word  or [numbers] or pluses


def examples(groups: Iterable[List[T]]) -> Iterable[T]:
    for group in groups:
        yield group[0]


# Note: T must be a dictionary type.
def grouped_by(seq: Iterable[T], path: str) -> Iterable[List[T]]:
    """
    Groups items by the given key (actually path to key).
    """
    return grouped(seq, key=lambda item: get_path(item, path))


def grouped(seq: Iterable[T], *, key) -> Iterable[List[T]]:
    """
    Group a sequence of items according to a function.
    :param seq:
    :param key:
    :return:
    """
    # Use a default empty list when encountering a new group.
    groups = OrderedDict()

    # Add each item to its corresponding group, creating group if it doesn't exist.
    for item in seq:
        k = str(key(item))
        if k in groups:
            groups[k].append(item)
        else:
            groups[k] = [item]

    # Return a sequence of groups.
    return list(groups.values())


def sorted_by(seq: Iterable[T], path: str, reverse=False) -> Iterable[T]:
    """
    Returns a list of objects sorted by the given key (path to key)
    """

    def key(obj):
        return get_path(obj, path)

    seq = list(seq)

    return sorted(seq, key=key, reverse=reverse)


def remove_duplicates(seq: Iterable[T], path: str) -> Iterable[T]:
    """
    Keep the first of each object which matches the key.
    """
    return remove_dups(seq, key=lambda e: e.get_path(path))


def remove_dups(seq: Iterable[T], *, key):
    already_seen = set()
    for e in seq:
        val = key(e)
        if val not in already_seen:
            already_seen.add(val)
            yield e


#######################################################################
#
# The following functions are no longer needed to "massage" the designs into usable form.
#
#######################################################################


def elevate(d: dict, key: str) -> dict:
    """
    Raise the attributes under the key to the top level.
    For example,
         elevate( {foo:bar, param: {hello: good day}}, "param"}})
         returns {foo: bar, hello: good day}
    """
    new_d = {
        **{k: v for k, v in d.items() if k != key},
        **({k: v for k, v in d[key].items()} if key in d else d),
    }
    return type(d)(new_d)


def a_to_d(array: [], key: str) -> dict:
    """
    Convert array to dictionary, where each item has the specified key.
    :param array: An array of items with a common key
    :param key: The name of key field
    :return: mapping key: item
    """
    return {item[key]: item for item in array}


def omap(fn: callable, obj):
    """
    Recursively transform each element of an object, building a new object from bottom to top.
       Note: This routine helps update immutable object trees.
    :param obj:
    :param obj: The object to transform.
    :param fn: A function to apply to each element of the object tree.
    :return: The transformed object.
    """

    # Recursively map each value in map
    if isinstance(obj, dict):
        val = type(obj)({k: omap(fn, v) for k, v in obj.items()})

    # Recursively map each item in an array
    elif isinstance(obj, list):
        val = type(obj)([omap(fn, v) for v in obj])

    # Primitives will also be modified, but not at this line.
    else:
        val = obj

    # Modify the resulting value, including primitives
    new = fn(val)

    return new


def merge_trees(dest, src):
    """
    Merges the leaf values from a src object into a destination objewct
    """
    # Take all the leaf values from the source and insert into the destination
    for value, path in scan_leaves(src):
        set_path(dest, path, value)


def scan_leaves(obj, path=""):
    """
    Generate a sorted sequence of (path, value) pairs for all leaf values in the object.
      Note: Useful for comparing JSON structures in unit tests.
      (generate (path,value) pairs and compare or diff)
    """

    # CASE: map.  fetch leaves of each value.  Sort them so similar objects generate same sequence.
    if isinstance(obj, dict):
        for (k, v) in sorted(obj.items()):
            yield from scan_leaves(obj[k], f"{path}.{k}")

    # CASE: list. Fetch leaves of each list item.
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            yield from scan_leaves(item, f"{path}[{index}]")

    # Otherwise: we are a primitive and a leaf. Return our value and our path.
    else:
        yield (obj, path)
