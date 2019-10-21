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

from os.path import dirname
from importlib import import_module

from scribble.importer import addImportPath, JinjaFileLoader
from scribble.model import Snippet, Element

DIR = dirname(__file__)


# Configure to load snippets from Test directory (type=test_files)
def test_init():
    JinjaFileLoader.install()
    addImportPath(f"{DIR}/testdoc_directory")


def test_import_py():
    module = import_module("components.MyComponent.function_snippet")
    assert module.__name__ == "components.MyComponent.function_snippet"


def test_import_jinja2():
    module = import_module("components.MyComponent.template_snippet")
    assert module.__name__ == "components.MyComponent.template_snippet"


def test_function_snippet():
    scope = Element.from_obj({"title": "Hello", "_types": ["MyComponent"]})
    text = Snippet("function_snippet", scope, subtitle="World")
    assert f"{text}" == "Hello World!"


def xtest_jinja_snippet():
    scope = Element.from_obj({"title": "Hello", "_types": ["MyComponent"]})
    text = Snippet("template_snippet", scope, subtitle="World")
    assert f"{text}" == "Hello World!\n\n"
