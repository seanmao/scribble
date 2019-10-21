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

import importlib
from typing import Tuple
from importlib.util import spec_from_file_location, module_from_spec
import os as _os
import sys


# TODO: use the public import files for importlib
from importlib._bootstrap_external import PathFinder, FileFinder

# Use the following for debugging
# from scribble.Test.PathFinder import PathFinder, JinjaFinder as FileFinder

from importlib._bootstrap_external import SourceFileLoader
from importlib._bootstrap_external import _get_supported_file_loaders
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec
from os.path import basename, splitext
from typing import List, Any


############################################################
#
# Interfaces into the Python import library.
#
# The primary entry point is "import_function", which
#    dynamically loads a module and returns the class or function
#    with the given name.
#
# This file also contains two hooks into the import library.
#  1) Create a Python "name space" which allows a module
#     to be found in one of several directories.
#     This enables third party documentation to be located
#     in separate directories than the regular sifive documentation.
#  2) Load Jinja templates as though they were conventional
#     Python modules.
#     Loader "hooks" are documented in Python's
#     import library, but they are not well implemented and
#     do not work as advertised. Making this work required
#     creating a modified "FileFinder".
#
# Mainly because of the problems with the import library's
#     loader "hooks", we should look at other ways of treating
#     jinja templates as Python functions. Alternatively, we could
#     work with Python import lib developers to help them fix the problem.
#
# TODO?: Get rid of importlib hooks and move logic to user-space.
#
##########################################################


def import_function(section_path: str, function_name: str = "") -> Tuple[callable, Any]:
    """
    Dynamically load a Python module and return the address of a function.
    :param section_path: The full path to the module eg. a.b.c
    :param function_name: The name of the function we want.
    :return: a function pointer  and the module which implements it.
    """
    # By default, the function name matches the last component
    if function_name == "":
        function_name = section_path.rpartition(".")[2]

    # Load the module and look up the function name.
    module = importlib.import_module(section_path)

    if not hasattr(module, function_name):
        raise FunctionNotFoundError(
            f"Module {section_path} does not contain function {function_name}"
        )
    # Since function name matches module name, we may get a module instead of a function.
    #   If so, then try again.
    fn = getattr(module, function_name)
    if not callable(fn):
        raise FunctionNotFoundError(f"path={section_path}  function={function_name}")

    return fn, module


class FunctionNotFoundError(ImportError):
    pass


def execute_function(
    section_path: str, function_name: str = "", *args, **kwargs
) -> Any:
    """
    As above, but invoke the function.
    """

    # Load the module and get the corresponding function
    fn, _ = import_function(section_path, function_name)

    # Invoke the section, which generally returns an iterator
    return fn(*args, **kwargs)


def addImportPath(*dirs):
    """
    Add paths to the module lookup paths  (sys.paths)
    """
    sys.path = [*dirs, *sys.path]


#####################################################################################
#
# The following importlib hooks are being obsoleted in favor of doing equivalent lookup
#   in user code.
#
#####################################################################################


class NamespaceCreator(MetaPathFinder):
    """
    Creates a dummy Python namespace for loading files from alternate directories.
      Uses 3.3+ "MetaFinder" from importlib to redirect the module search.
      Installs itself automatically upon creation.
    """

    namespace: str
    dirs: List[str]

    def __init__(self, namespace: str, *dirs: str):
        """
        Install self as an importlib Meta Finder which gets called before searching for files.
        :param namespace: The name space to create, eg scribble.snippets
        :param dirs: List of directories to search for submodules.
        """
        super().__init__()
        self.namespace = namespace
        self.dirs = dirs
        sys.meta_path.insert(
            0, self
        )  # Should come before Jinja metafinder, which is appended.

    def find_spec(self, name, path=None, module=None):

        # if name space matches, create a namespace module which searches the desired directories.
        if name == self.namespace:
            spec = ModuleSpec(name, None, is_package=True)
            spec.submodule_search_locations = self.dirs

        else:
            spec = None

        # print(f"NamespaceCreator.find_spec: name={name} path={path} spec={spec}")
        return spec


class JinjaFileLoader(SourceFileLoader):
    """
    Hook into the Python importlib to load .jinja files as python functions.

    Encountered a bug in PathFinder which cached only one loader per directory,
    which meant we couldn't load .jinja2 and .py files from the same
    directory. Created FixedupPathFinder which disables the
    cache. Since all file lookups are already cached elsewhere, the disabled
    cache isn't really necessary for performance. It is probably
    a holdover from the past.

    Additionally, the hook must process all the existing file types
    along with .jinja2 files. Ideally, the regular finder would
    process those. There seems to be some overly aggressive
    caching going on.
    """

    @classmethod
    def install(cls):
        # Add the jinja loader to the list of other loaders.
        tuples = [*_get_supported_file_loaders(), (cls, [".jinja2"])]

        sys.path_hooks.insert(0, FileFinder.path_hook(*tuples))
        sys.meta_path.insert(1, FixedupPathFinder)

    def get_data(self, fullname):
        """
        Produce a python wrapper around a template.
        The wrapper turns a jinja template into a python function.
        :param fullname: the name of template file.
        :returns: a Python function which invokes the template.
        """

        function_name = splitext(basename(fullname))[0]

        return f"""
from scribble.template import template
from scribble.model import Text, Element, Section, Snippet

def {function_name}(scope: Element, **kwargs: any) -> Text:
    newargs = {{k: v for k, v in kwargs.items() if k not in {"kwargs", "scope", "context"} }}
    text = template("{fullname}", scope=scope, kwargs=newargs, context=newargs, **newargs)

    return Text(text)
"""


class FixedupPathFinder(PathFinder):
    """
    Fixes a bug in importlib.
    PathFinder assumes there is only one loader installed per directory,
      so it keeps a cache   directory --> loader.
      The result is adding extra load hooks, say to load a new type of file,
      doesn't invoke the load hooks. The solution is to disable the cache.
      Since the file names for the directory are cached, shouldn't have much
      impact on performance.
    importlib is part of Python bootstrap, so it is difficult to debug.
    Test/PathFinder.py is a user-space copy of PathFinder for debugging.
    """

    @classmethod
    def _path_importer_cache(cls, path):
        """
        Get the finder for the path entry from sys.path_importer_cache.

        If the path entry is not in the cache, find the appropriate finder
        and cache it. If no finder is available, store None.
        """

        # print(f"path_importer: path={path}")
        if path == "":
            try:
                path = _os.getcwd()
            except FileNotFoundError:
                # Don't cache the failure as the cwd can easily change to
                # a valid directory later on.
                return ImportError()
        #######################################
        # try:
        #    finder = sys.path_importer_cache[path]
        # except KeyError:
        #    finder = cls._path_hooks(path)
        # sys.path_importer_cache[path] = finder
        #############################################

        # The original code is above. The next line is the new code.
        finder = cls._path_hooks(path)

        return finder


class ImportException(Exception):
    pass


#################################
#
# Prototype code for namespace mapping in userspace instead of the importlib.
#
# def import_module(section_path: str):
#     newpath = ModuleFinder.lookup_path(section_path)
#     module = importlib.import_module(newpath)
#    return module
#
#
# class ModuleFinder:
#     """
#     Based on the lead namespace, search a list of namespaces and translate the module path.
#     """
#
#     finder: Dict[str, List[str]] = dict()
#
#     @classmethod
#     def set_namespace(cls, namespace: str, searchList: List[str]):
#         cls.finder[namespace] = searchList
#
#     @classmethod
#     def lookup_path(cls, module: str) -> str:
#
#         # separate the module path into a leading namespace and a remaining subpath
#         namespace, subpath = module.split(".", 1)
#
#         # Done if the namespace isn't being translated.
#         if namespace not in cls.finder:
#             return module
#
#         # search the possible namespaces to find a valid section
#         for namespace in cls.finder[namespace]:
#             newpath = namespace + "." + subpath
#             if import_function(newpath) is not None:  # TODO: May want to cache.
#                 return newpath
#
#         raise ImportException(f"Section finder - unable to find {module} in {cls.finder.keys()}")
#


def LoadSourceFile(functionName: str, moduleName: str, filePath: str):
    """
    Load a module with the given name from a file at a given location.
       An alternate primitive, which can be used to reimplement above without importlib hooks.
    :param moduleName:
    :param filePath:
    :return: None if can't find it.
    """

    # If the file exists,
    if not _os.path.isfile(filePath):
        return None

    # Create a module from the file
    spec = spec_from_file_location(moduleName, filePath)
    module = module_from_spec(spec)

    # Load the module
    spec.loader.exec_module(module)

    # Look up the specified function.
    fn = getattr(module, functionName, None)
    return fn
