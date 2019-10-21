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

import os
from os.path import dirname
from pathlib import Path
from scribble.path_interpolation import initPathInterpolation, pathLookup


def tryit(path, expected):
    interpolated = pathLookup(path)
    assert interpolated == expected


def abs(path):
    return str(Path(path).absolute())


def test_relative_paths():

    # Get pwd and our test directory.
    here = dirname(__file__)
    pwd = os.getcwd()
    assert isinstance(here, str) and isinstance(pwd, str)

    initPathInterpolation(pwd=pwd)

    assert pathLookup("/xxx") == "/xxx"
    assert pathLookup("xxx") == abs("xxx")
    assert pathLookup("{pwd}") == pwd
    assert pathLookup("{pwd}/xxx") == f"{pwd}/xxx"

    assert pathLookup("{here}/mystuff", here=here, extra="extra") == f"{here}/mystuff"
    assert pathLookup("{here}/mystuff", __file__) == f"{here}/mystuff"


def test_nested_paths():
    morePaths = dict(
        config="{pwd}/{there}/something",
        there="{somewhereElse}/theirplace",
        somewhereElse="{where}",
        where="myplace",
    )
    assert pathLookup("{config}", **morePaths) == abs("myplace/theirplace/something")


def test_initial_here():  # One of the initial paths has {here} in it.
    here = dirname(__file__)
    initPathInterpolation(here, otherpath="{here}/other")
    assert pathLookup("{otherpath}") == f"{here}/other"
