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
)  # flake8: noqa F821 - Allows early access to class name

from contextlib import suppress
from os.path import splitext
from typing import Iterable, List, Callable, Tuple, Any

from scribble.exceptions import DocumentException, SnippetNotFound
from scribble.importer import FunctionNotFoundError
from scribble.importer import import_function
from scribble.scope import Element
from scribble.template import template
from scribble.template import template_string


#################################################################
# A "Section" is the primary concept for producing text.
#   It is simply a function which accepts a "scope" and extra parameters,
#   and produces Text.
#
# In reality, things are a bit more complicated.
#   Sections are
#     - dynamically loaded.
#     - consist of Python functions, Jinja templates, or both.
#     - can be a standalone file or a subdirectory
#     - addressed by absolute or "relative" module paths.
#     - the output Text is an iterator to strings, rather than a simple string,
#
# Every section is passed a "scope", the portion of the design tree it is intended to see.
#   There may be additional parameters which are passed as **kwargs.
#   One of the keyword parameters, "_curpath_" is implicitly passed to each section,
#   which means sections should always pass extra keyword parameters on to their subsections.
#   "_curpath_" is a minor piece of "magic" which allows relative path names.
#   To allow templates to pass on extra kwargs, the variable "kwargs" is declared explicitly.
#
# Note it is transparent to the caller whether Section, Snippet, Template are classes or
#   functions. Since they started out as classes, they retain their original capitalization.
#
########################################################################


def Section(path: str, scope: Element, **kwargs) -> Text:
    """
    Invoke a section by its module name, pass parameters and return Text.
       Section is the universal wrapper around all scribble sections.

    :param path: module path to the function which implements the section
    :param scope: the primary element the section addresses.
    :param kwargs: a list of keyword parameters passed through to the section.
    """

    # load the section and invoke it.
    fn, _ = load_section(path, scope, **kwargs)
    return fn()


def load_section(
    path: str, scope: Element = None, *, _curpath_=None, _file_=None, **kwargs
) -> Tuple[Callable, Any]:
    """
    Load the function associated with a section, but dont invoke it.
    Separating loading from executing allows better error reporting when a
    subsequent subsection can't be found. Also, by returning a function with
    parameters already bound, all of the relative path processing can take
    place in this one function.
    """
    # Note the role of _curpath_ and _file_
    #  - contains the modulepath and filename of the current section being processed.
    #  - passed implicitly as part of kwargs.  (Thus, all sections must pass on **kwargs)
    #  - set to new value whenever a new section is invoked.
    #  - needed to calculate absolute path of a relative path reference.

    # Convert relative path to absolute path. Assumes _curpath_ is set.
    if path[0] == ".":
        if _curpath_ is None:
            raise DocumentException(
                f"Invoking Section {path} with relative path, but don't know current path."
            )
        path = _curpath_.rsplit(".", 1)[0] + path

    # By convention, we invoke a function with the same name as module.
    function_name = path.rpartition(".")[2]

    # Try to load the function,
    try:
        fn, module = import_function(path, function_name)

    # If not found, try loading from subdirectory of same name.
    except (ModuleNotFoundError, FunctionNotFoundError):
        path = f"{path}.{function_name}"
        fn, module = import_function(path, function_name)

    # Return a function which binds _curpath_,
    #   We may as well bind everything or somebody could introduce inconsistencies.
    return (
        lambda: Text(fn(scope, _curpath_=path, _file_=module.__file__, **kwargs)),
        module,
    )


def Snippet(snippet_name: str, scope: Element, **kwargs) -> Text:
    """
    Find the appropriate section for the type of element and invoke it.
    :param snippet_name: The module name we are searching for, usually its role in a document.
    :param scope: The element the section addresses. It's type defines the search.
    :param kwargs: additional parameters passed to the section.
    :return: Text
    """
    # Find the module path to the best section for processing this element.
    paths = list(snippet_paths(snippet_name, scope._types))

    # Find the first section which can be loaded.
    for path in paths:
        with suppress(ModuleNotFoundError, FunctionNotFoundError):
            fn, _ = load_section(path, scope, **kwargs)
            break

    # if none, error.
    else:
        raise SnippetNotFound(
            f"No snippet {snippet_name} found for types {scope._types}"
        )

    # Invoke the section's function. Note we are no longer suppressing NotFound errors.
    return fn()


def StringTemplate(
    template: str, scope: Element, *, _curpath_=None, kwargs=None, **kargs
) -> Text:
    """
    From within a python based Section, fill in a jinja template which is given as a string.
    """
    newargs = {k: v for k, v in kargs.items() if k not in {"kwargs", "scope"}}
    text = template_string(template, scope=scope, kwargs=newargs, **newargs)
    return Text([text])


def PairedTemplate(caller_filename: str, scope: Element, **kwargs) -> Text:
    """
    Invoke the template which is paired up to a Python function.
      A complex document section can consist of both a Python function and a Jinja template.
      The Python function and the template have similar file names, and both live in the same
      directory. Given the file name of the Python function, PairedTemplate invokes the
      Jinja template with a similar name.
    """
    # The path to the template is identical to the function's file name,
    # but with ".jinja2" extension.
    file_name = (
        splitext(caller_filename)[0] + ".jinja2"
    )  # TODO: Unify file path handling.

    newargs = {k: v for k, v in kwargs.items() if k not in {"kwargs", "scope"}}
    text = template(file_name, scope=scope, kwargs=newargs, **newargs)
    return Text(text)


class Text(Iterable[str]):
    """
    An iterator of text fragments (ie strings).
       Text is the output of all document sections. Generally text fragments will be written
       to a device or a file, but this class converts Text to a single string when requested.
       As a convenience, strings can be passed in as multiple parameters.
       Thus, Text(["a", "b"]) can be simplified to Text("a", "b")
    """

    items: Iterable[str]

    def __init__(self, *items):
        """
        To provide flexibility in how a section is implemented, creates a Text stream from:
          - an iterable of strings
          - multiple strings
          - another Text object
        """
        # CASE: all parameters are strings --> iterate through the strings.
        if all(isinstance(item, str) for item in items):
            self.items = items

        # CASE: We were passed a Text object --> move the iterator instead of rewrapping Text.
        elif len(items) == 1 and isinstance(items[0], Text):
            self.items = items[0].items

        # CASE: We were passed an iterable --> just wrap the iterable.
        elif len(items) == 1 and isinstance(items[0], Iterable):
            self.items = items[0]

        # OTHERWISE, error
        else:
            raise DocumentException(f"Unable to interpret items as Text {items}")

    ################################################################
    # We are a proxy for an iterable, so implement those interfaces.
    #   Note the __str__ function merges the text into a string.
    ###############################################################

    def __iter__(self):
        return iter(self.items)

    def __str__(self):
        return "".join(self)


def text(f):
    """
    Function decorator so a section returns Text
    instead of iter(str) or str.
    """

    def wrapper(*args, **kwargs) -> Text:
        return Text(f(*args, **kwargs))

    return wrapper


def snippet_paths(snippet_name: str, types: List[str]) -> Iterable[str]:
    """
    List all the module paths where a snippet module might be found.
    :param snippet_name: The base module name (corresponding to its role in document).
    :param types: A search list of types for finding a module.
    :return: A list of module names to try.
    """

    # For each of the possible types, most specific to more general
    for type in types:
        yield f"components.{type}.{snippet_name}"
