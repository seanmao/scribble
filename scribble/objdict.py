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

from __future__ import (
    annotations,
)  # flake8: noqa F821 - Allows access to class name from within.

from datetime import date
from numbers import Number

import scribble.config_file as config
from scribble.exceptions import DocumentException
from scribble.obj import subtrees, set_path, get_path

MISSING = ""  # For debugging - save name of missing key


def keepers(d: dict) -> dict:
    """
    filters out the "None" values from a dictionary
    """
    keep = {k: v for k, v in d.items() if v is not None}
    return keep


# Future: extend to include arrays, which could be referenced by index or by "._n" attribute.


class SimpleObjdict(dict):
    """
    A dictionary which can be accessed like an object, and which returns None by default.

    """

    ##########################################################
    # Wrapper functions which implement a shallow dictionary
    ##########################################################

    def __init__(self, old: dict = {}, **kwargs: dict):
        obj = {**{k: v for k, v in old.items() if k not in kwargs}, **kwargs}
        super().__init__(keepers(obj))

    def __getattr__(self, key: str) -> any:
        return self[key]

    def __setattr__(self, key: str, value: any):
        self.update({key: value})

    def __delattr__(self, key):
        del self[key]

    def __missing__(self, key):
        """
        Return a value which is False-ish and raises exception when printed.
        Allows us to test a chain of references, but only fail when printing
        """
        global MISSING
        MISSING = key  # For debugging - save name of missing key
        return INVALID

    def __bool__(self):
        return self != {}

    def update(self, other={}, **kwargs):
        """
        Does the real work of setting values.
        """
        joined = dict(other, **kwargs)

        # Update with the new set of k:v pairs,
        #   but delete existing keys which are being assigned the value of None
        for k, v in joined.items():
            if v is None:
                if k in self:
                    del self[k]
            else:
                self[k] = v


class Objdict(SimpleObjdict):
    """
    A class of objects where fields can be referenced as either dictionaries or objects.
    For example,
         obj["field"] and obj.field are equivalent.
    If a field is not defined, then it returns the value None rather than throwing an exception.

    This is a recursive structure where all subobjects and subdictionaries
    are converted to Objdicts. The primary method to recursively convert an object to Objdict is:
         odict = Objdict.from_object(obj)

    The regular Objdict constructor does a non-recursive build from keyword arguments.
         Objdict(k1=v1, k2=v2 ...) # does NOT convert v1, v2 ...

    TODO: get rid of SimpleObjDict and handle recursion properly in the main constructor.
    TODO: add a falsish "missing node" when looking up chains of references to prevent exceptions.
    TODO: ensure the "missing node" throws an exception when converted to string.
    """

    @classmethod
    def from_obj(cls, obj: any) -> Objdict:
        """
        Recursively convert an object to object dictionaries, even if embedded in lists.
          Used primarily for accessing configurations, so it doesn't need to convert class objects.
        """
        # CASE: list. Convert each item in the list.
        if isinstance(obj, list):
            value = [cls.from_obj(item) for item in obj]

        # CASE: dictionary. Convert each item in the dictionary.
        elif isinstance(obj, dict):
            d = {k: cls.from_obj(v) for k, v in obj.items()}
            value = cls(**d)

        # CASE: basic number or string. Use the item "as is"
        elif (
            isinstance(obj, str)
            or isinstance(obj, Number)
            or isinstance(obj, date)
            or obj is None
        ):
            value = obj

        # CASE: object with an internal dictionary. Treat like a dictionary.
        elif hasattr(obj, "__dict__"):
            value = cls.from_obj(obj.__dict__)

        # OTHERWISE: we need to figure it out.
        else:
            raise DocumentException(f"Objdict.from_dict: can't convert value {obj}")

        return value

    @staticmethod
    def to_dict(obj):
        """
        Convert an object dictionary object back to an object using dictionaries
          Note: Needed for json serialization. It indicates Objdict is not quite perfect.
        :param obj:
        :return:
        """
        if isinstance(obj, dict):
            value = {k: Objdict.to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            value = [Objdict.to_dict(v) for v in obj]
        else:
            value = obj
        return value

    @classmethod
    def read(cls, filename: str) -> Objdict:
        """
        Read a configuration file as a new object.
        """
        obj = config.read(filename)
        return cls.from_obj(obj)

    def write(self, filename: str):
        """
        Write current object as a configuration file.
        """
        obj = self.to_dict(self)
        config.write(obj, filename)

    ###############################################################################
    #
    # The following methods are wrappers around the corresponding object functions.
    #
    ###############################################################################

    def get_path(self, key):
        """
        Fetch a value from current scope, given a path to the value.
        """
        return get_path(self, key)

    def set_path(self, key, value):
        """
        Set a value from current scope, given a path the the value.
         Note currently being used, but will be part of Errata
        """
        return set_path(self, key, self.from_obj(value))

    def subtrees(self):
        """
        Return a stream of all subtrees of the current scope.
           Used for searching and querying subtrees.
        """
        yield from subtrees(self)


class InvalidObject:
    """
    An empty object which is falsish, returns itself on reads, and dies when printed.
    """

    def __getattr__(self, key: str):
        return INVALID

    def __getitem__(self, index: int):
        return INVALID

    def __str__(self):
        raise DocumentException(
            f"Attempting to display a non-existent value MISSING={MISSING}"
        )

    def __bool__(self):
        return False

    def __eq__(self, other):
        return other is INVALID or other is None

    def __next__(self):
        raise DocumentException(
            f"Attempting to iterate a non-existent value MISSING={MISSING}"
        )

    def __iter__(self):
        return iter([])

    @property
    def _missing(self):
        return MISSING  # For display in debugger


# Create a singleton object which can be referenced, but can't be displayed.
INVALID = InvalidObject()
