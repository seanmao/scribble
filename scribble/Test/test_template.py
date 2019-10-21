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

from scribble.model import Element
from scribble.template import template

DIR = f"{dirname(__file__)}"


def test_template():

    # Load a template and process it.  We are re-using the template from the snippet test.
    scope = Element(dict(title="Hello"))  # TODO: get better constructor for Element
    text = template(
        f"{DIR}/testdoc_directory/components/MyComponent/template_snippet.jinja2",
        scope=scope,
        subtitle="World",
    )
    assert f"{text}" == "Hello World!\n\n"
