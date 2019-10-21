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

import importlib._bootstrap as _bootstrap
import os as _os
import sys
from importlib._bootstrap_external import _NamespacePath, _path_stat
from importlib._bootstrap_external import (
    _path_join,
    _path_isfile,
    _path_isdir,
    FileFinder,
)


# Finders #####################################################################


class PathFinder:
    """Meta path finder for sys.path and package __path__ attributes."""

    @classmethod
    def invalidate_caches(cls):
        """Call the invalidate_caches() method on all path entry finders
        stored in sys.path_importer_caches (where implemented)."""
        for name, finder in list(sys.path_importer_cache.items()):
            if finder is None:
                del sys.path_importer_cache[name]
            elif hasattr(finder, "invalidate_caches"):
                finder.invalidate_caches()

    @classmethod
    def _path_hooks(cls, path):
        """Search sys.path_hooks for a finder for 'path'."""
        if sys.path_hooks is not None and not sys.path_hooks:
            _warnings.warn("sys.path_hooks is empty", ImportWarning)
        for hook in sys.path_hooks:
            try:
                print(f"_path_hooks: {hook}({path})")
                h = hook(path)
                print(f"PathFinder hook returned {h}")
                return h
            except ImportError:
                print(f"PathFinder hook raised ImportError")
                continue
        else:
            return None

    @classmethod
    def _path_importer_cache(cls, path):
        """Get the finder for the path entry from sys.path_importer_cache.

        If the path entry is not in the cache, find the appropriate finder
        and cache it. If no finder is available, store None.

        """
        if path == "":
            try:
                path = _os.getcwd()
            except FileNotFoundError:
                # Don't cache the failure as the cwd can easily change to
                # a valid directory later on.
                return None
        print(
            f"PathFinder._path_importer_cache path={path}  in?={path in sys.path_importer_cache}"
        )
        try:
            finder = sys.path_importer_cache[path]
        except KeyError:
            finder = cls._path_hooks(path)
            sys.path_importer_cache[path] = finder

        print(f"PathFinder.path_importer_cache (done) - finder={finder}")
        return finder

    @classmethod
    def _legacy_get_spec(cls, fullname, finder):
        print(f"legacy_get_spec -- SHOULDNT BE HERE")
        # This would be a good place for a DeprecationWarning if
        # we ended up going that route.
        if hasattr(finder, "find_loader"):
            loader, portions = finder.find_loader(fullname)
        else:
            loader = finder.find_module(fullname)
            portions = []
        if loader is not None:
            return _bootstrap.spec_from_loader(fullname, loader)
        spec = _bootstrap.ModuleSpec(fullname, None)
        spec.submodule_search_locations = portions
        return spec

    @classmethod
    def _get_spec(cls, fullname, path, target=None):
        """Find the loader or namespace_path for this module/package name."""
        # If this ends up being a namespace package, namespace_path is
        #  the list of paths that will become its __path__
        print(f"PathFinder._get_spec (entry) fullname={fullname} path={path}")
        namespace_path = []
        for entry in path:
            print(f"PathFinder: entry={entry}")
            if not isinstance(entry, (str, bytes)):
                continue
            finder = cls._path_importer_cache(entry)
            print(f"PathFinder._get_spec: finder={finder}")
            if finder is not None:
                if hasattr(finder, "find_spec"):
                    print(
                        f"PathFinder._get_spec: calling finder.find_spec({fullname}, {target})"
                    )
                    spec = finder.find_spec(fullname, target)
                else:
                    spec = cls._legacy_get_spec(fullname, finder)
                if spec is None:
                    continue
                if spec.loader is not None:
                    return spec
                portions = spec.submodule_search_locations
                if portions is None:
                    raise ImportError("spec missing loader")
                # This is possibly part of a namespace package.
                #  Remember these path entries (if any) for when we
                #  create a namespace package, and continue iterating
                #  on path.
                namespace_path.extend(portions)
        else:
            spec = _bootstrap.ModuleSpec(fullname, None)
            spec.submodule_search_locations = namespace_path
            return spec

    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        print(f"PathFinder.find_spec({fullname}, {path}) - called")
        """Try to find a spec for 'fullname' on sys.path or 'path'.

        The search is based on sys.path_hooks and sys.path_importer_cache.
        """
        if path is None:
            path = sys.path
        spec = cls._get_spec(fullname, path, target)
        print(f"PathFinder.     spec={spec}")
        if spec is None:
            return None
        elif spec.loader is None:
            namespace_path = spec.submodule_search_locations
            if namespace_path:
                # We found at least one namespace path.  Return a spec which
                # can create the namespace package.
                spec.origin = None
                spec.submodule_search_locations = _NamespacePath(
                    fullname, namespace_path, cls._get_spec
                )
                return spec
            else:
                return None
        else:
            return spec

    @classmethod
    def find_module(cls, fullname, path=None):
        """find the module on sys.path or 'path' based on sys.path_hooks and
        sys.path_importer_cache.

        This method is deprecated.  Use find_spec() instead.

        """
        spec = cls.find_spec(fullname, path)
        if spec is None:
            return None
        return spec.loader


class JinjaFinder(FileFinder):
    def __init__(self, *loader_details):
        print(f"new JinjaFinder({loader_details})")
        super().__init__(*loader_details)

    @classmethod
    def path_hook(cls, *loader_details):
        """A class method which returns a closure to use on sys.path_hook
        which will return an instance using the specified loaders and the path
        called on the closure.

        If the path called on the closure is not a directory, ImportError is
        raised.

        """

        def path_hook_for_JinjaFinder(path):
            """Path hook for importlib.machinery.FileFinder."""
            print(f"JinjaFinder.path_hook({path}) details={loader_details}")

            if not _path_isdir(path):
                raise ImportError("only directories are supported", path=path)
            return cls(path, *loader_details)

        return path_hook_for_JinjaFinder

    def __repr__(self):
        return f"JinjaFinder(path={self.path}  loaders={self._loaders})"

    def find_spec(self, fullname, target=None):
        """Try to find a spec for the specified module.

        Returns the matching spec, or None if not found.
        """
        print(f"JinjaFinder.find_spec({fullname}  path={self.path})")
        is_namespace = False
        tail_module = fullname.rpartition(".")[2]
        try:
            mtime = _path_stat(self.path or _os.getcwd()).st_mtime
        except OSError:
            mtime = -1
        if mtime != self._path_mtime:
            self._fill_cache()
            self._path_mtime = mtime
        # tail_module keeps the original casing, for __file__ and friends
        if _relax_case():
            cache = self._relaxed_path_cache
            cache_module = tail_module.lower()
        else:
            cache = self._path_cache
            cache_module = tail_module
        # Check if the module is the name of a directory (and thus a package).
        print(
            f"JinjaFinder.find_spec  - looking in cache for {cache_module}  {cache_module in cache}"
        )
        if cache_module in cache:
            base_path = _path_join(self.path, tail_module)
            for suffix, loader_class in self._loaders:
                init_filename = "__init__" + suffix
                full_path = _path_join(base_path, init_filename)
                print(f"   Looking for file {full_path}")
                if _path_isfile(full_path):
                    return self._get_spec(
                        loader_class, fullname, full_path, [base_path], target
                    )
            else:
                # If a namespace package, return the path if we don't
                #  find a module in the next section.
                is_namespace = _path_isdir(base_path)
        # Check for a file w/ a proper suffix exists.
        for suffix, loader_class in self._loaders:
            full_path = _path_join(self.path, tail_module + suffix)
            print(f"  -- full_path={full_path}   loader_class={loader_class} ")
            if (cache_module + suffix) not in cache:
                print(f"   {cache_module+suffix} not in cache {cache}")
            _bootstrap._verbose_message("trying {}", full_path, verbosity=2)
            if cache_module + suffix in cache:
                if _path_isfile(full_path):
                    print(
                        f"    - about to call _get_spec({loader_class}, {fullname}, {full_path})"
                    )
                    return self._get_spec(
                        loader_class, fullname, full_path, None, target
                    )
        if is_namespace:
            _bootstrap._verbose_message("possible namespace for {}", base_path)
            spec = _bootstrap.ModuleSpec(fullname, None)
            spec.submodule_search_locations = [base_path]
            return spec
        return None


class NewPathFinder(PathFinder):
    @classmethod
    def _path_importer_cache(cls, path):
        """Get the finder for the path entry from sys.path_importer_cache.

        If the path entry is not in the cache, find the appropriate finder
        and cache it. If no finder is available, store None.

        """
        print(f"path_importer_cache path={path}  in?={path in sys.path_importer_cache}")
        if path == "":
            try:
                path = _os.getcwd()
            except FileNotFoundError:
                # Don't cache the failure as the cwd can easily change to
                # a valid directory later on.
                return None
        # try:
        #    finder = sys.path_importer_cache[path]
        # except KeyError:
        finder = cls._path_hooks(path)
        # sys.path_importer_cache[path] = finder
        return finder


_CASE_INSENSITIVE_PLATFORMS_STR_KEY = ("win",)
_CASE_INSENSITIVE_PLATFORMS_BYTES_KEY = "cygwin", "darwin"
_CASE_INSENSITIVE_PLATFORMS = (
    _CASE_INSENSITIVE_PLATFORMS_BYTES_KEY + _CASE_INSENSITIVE_PLATFORMS_STR_KEY
)


def _relax_case():
    """True if filenames must be checked case-insensitively."""
    return False


class _warnings:
    def warn(self, msg: str, level=None):
        print(f"Warning: {str}")
