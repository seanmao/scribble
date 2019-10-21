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

from os.path import abspath, dirname


# Nothing which restricts it to paths.
class Interpolator:
    def __init__(self, **kwargs):
        """
        Create an Interpolator by passing it a bunch of key value pairs.
        """
        self.lookups = kwargs

    def update(self, **kwargs):
        """
        Add new key-value pairs, superseding any old values.
        """
        self.lookups = dict(
            self.lookups, **kwargs
        )  # Note: don't alter original dictionary.

    def format(self, string: str, **kwargs) -> str:
        """
        Interpolate a string. Since the replacement value may also contain interpolations, repeat.
        """
        # If the string is empty, just return it as is. (support None, Undefined, ...)
        if not string:
            return string

        # Merge passed key-values into a common dictionary
        merged = dict(self.lookups, **kwargs)

        # Repeat interpolating until the string stops changing
        prev = ""
        while string != prev:
            prev = string
            string = string.format(**merged)

        return string


def initPathInterpolation(here=None, **kwargs):
    """
    Initialize an interpolator specifically for file system paths.
    """
    # Replace {here} as we initialize things - {here} will change or be undefined in the future.
    #  Do not change other interpolations, so do a string substitution rather than format.
    newArgs = (
        kwargs
        if here is None
        else {k: v.replace("{here}", here) for k, v in kwargs.items()}
    )

    global pathInterpolator
    pathInterpolator = Interpolator(**newArgs)


def pathLookup(path: str, _file_=None, **kwargs) -> str:
    """
    Interpolate a file system path, returning an absolute path.
    If _file_ is set, then {here} is set to the directory of the file.
    """
    # if _file_ was set, add {here}<-directory to the path interpolations.
    kwargs = dict(kwargs, here=dirname(_file_)) if _file_ else kwargs

    # Interpolate the path, and return the absolute version of it.
    newPath = pathInterpolator.format(path, **kwargs)
    return abspath(newPath)
