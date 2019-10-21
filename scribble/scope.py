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
import re
from pathlib import Path
from typing import Iterable, List, Optional

from scribble.exceptions import DocumentException
from scribble.obj import sorted_by, grouped_by, grouped, examples, remove_duplicates
from scribble.objdict import Objdict, INVALID
from scribble.template import NON_BREAKING_HYPHEN

PROJDIR = Path(__file__).parent.parent


class Element(Objdict):
    """
    An Element is a portion of the design tree.  It says where a section is focused.
    Note elements generally have a "_types" list saying what type it is.
    """

    def primary_type(self) -> str:
        return self._types[0]

    # A replacement for primary_type()
    @property
    def _type(self) -> str:
        return self._types[0]

    @property
    def documentationType(self) -> str:
        """
        Use the "_type" property to generate a plausible documentation string for the type.
          (Works for some common cases - need a more general solution,probably based on schemas)
        """

        # Break CamelCase into separate words Camel Case.
        #  (We assume underscores in a type are between two uppercase letters)
        dt = re.sub("([A-Z][A-Z0-9_]*[a-z0-9_]*)", r" \1", self._type)

        # Replace underscores with hyphens.
        dt = dt.replace("_", NON_BREAKING_HYPHEN)

        # We may introduced a leading space. Delete it.
        #   TODO: (We should be able to do this as a single re.)
        dt = re.sub("^ ", "", dt)

        return dt

    def is_instance(self, *types: str) -> bool:
        """
        Is the element an instance of a type?
        :param types:
        :return:
        """
        return self._types and (set(self._types) & set(types))

    def is_not_instance(self, *types: str) -> bool:
        return self._types and not (set(self._types) & set(types))

    def query(self) -> QueryStream:
        """
        Start a query using the given design subtree.
        :return: A stream which can be "queried"
        """
        iterator = (s for s in self.subtrees() if isinstance(s, Element))
        return MemoizedQueryStream(iterator, self)


class QueryStream(Iterable[Element]):
    """
    A QueryStream supports queries against a design element and its subelements.
       It is implemented as a stream of element subtrees, which are filtered by query routines.
    """

    gen: Iterable[Element]

    def is_instance(self, *types: str) -> QueryStream:
        """
        Query to keep elements whose types are instances of the given type.
        """
        return QueryStream(e for e in self if e.is_instance(*types))

    def is_not_instance(self, *types: str) -> QueryStream:
        return QueryStream(e for e in self if e.is_not_instance(*types))

    def filter(self, fn):
        return QueryStream(e for e in self if fn(e))

    # TODO: one of several
    def contains_key(
        self, path: str
    ):  # Note: "has_key" generates lint deprecated warnings.
        """
        Selects elements with a specified piece of data present.
          :param path: A string path "a.b.c" representing a piece of data which must exist.
          """
        return QueryStream(e for e in self if e.get_path(path) is not None)

    # TODO: one of several
    def has_key_value(self, path: str, value: any) -> QueryStream:
        """
        Selects elements which have a specified data value.
        :param path: A string path "a.b.c" representing a piece of data
        :param value: The corresponding value which must match.
        """
        return QueryStream(e for e in self if e.get_path(path) == value)

    def hasnt_key_value(self, path: str, *values: any) -> QueryStream:
        """
        select elements which do NOT have any the specified values.
        """
        return QueryStream(e for e in self if e.get_path(path) not in values)

    def value_contains(self, path: str, value: any) -> QueryStream:
        def contains(e: Element) -> bool:
            container = e.get_path(path)
            return container and e in container

        return self.filter(contains)

    def debug(self):
        """
        Collects the stream into an array so it can be viewed in a debugger.
        :return - a stream with all of the original data.
        """
        lst = list(self)
        return QueryStream(lst)

    def examples(self, path: str) -> QueryStream:
        """
        Group elements by a value, then pick the first of each group as an example.
        """
        groups = self.grouped_by(path)
        return QueryStream(examples(groups))

    # TODO: Refactor so this is a query stream?
    def grouped_by(self, path: str) -> Iterable[List[Element]]:
        """
        Groups items by the given key (actually path to key).
        """
        return grouped_by(self, path)

    def grouped(self, *, key):
        return grouped(self, key=key)

    def sorted_by(self, path: str, reverse=False) -> QueryStream:
        return QueryStream(sorted_by(self, path, reverse))

    def sorted(self, *, key, reverse=False) -> QueryStream:
        return QueryStream(sorted(self, key=key, reverse=reverse))

    def sortgroup_by(self, path: str) -> Iterable[List[Element]]:
        return self.sorted_by(path).grouped_by(path)

    def remove_duplicates(self, path: str) -> QueryStream:
        """
        Keep the first of each element which matches the key.
        """
        return QueryStream(remove_duplicates(self, path))

    ##################################################################
    # "Collectors" to accumulate results of a query.
    #   They grab one or more of the query results at the end of the query.
    #   Note:
    #      - the stream itself represents results and can be used directly.
    #      - A "collector" is a destructive operation, and the stream is not
    #        valid for further queries or collectors.
    #
    # TODO: invalidate the stream and raise exception if stream is reused.
    ##################################################################

    def collect(self) -> List[Element]:
        """
        Collect all of the resulting units into a list.
        """
        return list(self)

    def first(self) -> Optional[Element]:
        """
        Grab the first unit of the stream, returning None if there aren't any.,
        """
        return next(self, INVALID)

    def one(self) -> Element:
        """
        Verify the stream has exactly one element and return it.
        """
        unit = self.optional()
        if unit is INVALID:
            raise DocumentException(f"scribble query 'one' encountered an empty list.")

        return unit

    def optional(self) -> Element:
        """
        Verify the stream has at most one element and return it (or None)
        """
        element = next(self, INVALID)
        if next(self, INVALID) is not INVALID:
            raise DocumentException(f"scribble query returned more than one choice")

        return element

    def exists(self) -> bool:
        return self.first() is not INVALID

    def count(self) -> int:
        return sum(1 for _ in self)

    def _invalidate(self):
        self.gen = None

    ################################################
    # Query stream serves as a proxy for the underlying iterator.
    #  (In Scala, we would pimp it with an implicit conversion.)
    ################################################
    def __init__(self, gen: Iterable[Element]):
        if gen is INVALID:
            raise DocumentException("Attempting to query an INVALID")

        if isinstance(gen, QueryStream):
            self.gen = gen.gen
        else:
            self.gen = iter(gen)

    def __next__(self):
        return self.gen.__next__()

    def __iter__(self):
        return self


# An alternate constructor for QueryStream.
def Query(elements: List[Element]) -> QueryStream:
    return QueryStream(elements)


# Reference path to the primary type of an element
#  Can be used for sorting or grouping elements.
primary_type = "_types[0]"


#########################################################################
# A query stream which memo-izes the first "is_instance" query.
#   The idea is to remember the results of
#         element.query().is_instance(xxx)
#   and to do the search only once.
#   (we could expand it to other queries, but is_instance is the most common case)
##################################################################################
class MemoizedQueryStream(QueryStream):
    memo = {}
    enabled = False

    def __init__(self, gen, element: Element):
        super().__init__(gen)
        self.element = element

    def is_instance(self, *types: str) -> QueryStream:

        if not self.enabled:
            return super().is_instance(*types)

        # Create a hashable tuple from the args.
        args = (id(self.element), *types)

        # If memo is full, empty it out and start over. (infrequent if at all)
        #  Note: this is a really lame replacement algorithm, but
        #  it works surprisingly well in practice.
        if len(MemoizedQueryStream.memo) > 1024:
            MemoizedQueryStream.memo = {}

        # Get results
        # CASE: already memoized. Return the saved results.
        if args in MemoizedQueryStream.memo:
            results = MemoizedQueryStream.memo[args]

        # OTHERWISE, scan for the results and save them
        else:
            results = super().is_instance(*types).collect()
            MemoizedQueryStream.memo[args] = results

        # Once we find the results, we may have additional queries appended onto the stream.
        #    Additional queries are not memoized, just the first "is_instance()"
        return QueryStream(results)

    @classmethod
    def enable(cls):
        cls.enabled = True
