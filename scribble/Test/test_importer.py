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

from importlib.util import find_spec
from os.path import dirname

from scribble.importer import (
    addImportPath,
    JinjaFileLoader,
    FixedupPathFinder,
    execute_function,
)
from scribble.model import Element

DIR = f"{dirname(__file__)}"
SCOPE = Element(title="Hello")


def test_init():  # Work in progress
    JinjaFileLoader.install()
    addImportPath(f"{DIR}/testdoc_directory")


# TODO: Doesn't work.  Not needed now, but should be tracked down.
def xtest_find_spec_function():
    spec = FixedupPathFinder.find_spec(
        "document.dummy_function", [f"{DIR}/testdoc_directory"]
    )
    assert spec.origin == f"{DIR}/testdoc_directory/document/dummy_function.py"


# TODO: Doesn't work.  Not needed now, but should be tracked down.
def xtest_find_spec_template():
    spec = FixedupPathFinder.find_spec(
        "document.dummy_template", [f"{DIR}/testdoc_directory"]
    )
    assert spec.origin == f"{DIR}/testdoc_directory/document/dummy_template.jinja2"


def test_find_spec_for_template():
    spec = find_spec("document.dummy_function")
    assert spec.origin == f"{DIR}/testdoc_directory/document/dummy_function.py"


def test_find_spec_for_function():
    spec = find_spec("document.dummy_template")
    assert spec.origin == f"{DIR}/testdoc_directory/document/dummy_template.jinja2"


def test_import_template():
    from document.dummy_template import dummy_template

    text = dummy_template(SCOPE, subtitle="World")
    # text = execute_function("scribble.snippet.dummy_template", SCOPE, subtitle="World")
    assert f"{text}" == "Hello World!\n\n"


# Dynamically load a function and execute it.
def test_function_execute():
    text = execute_function(
        "document.dummy_template", "dummy_template", SCOPE, subtitle="World"
    )
    assert f"{text}" == "Hello World!\n\n"
