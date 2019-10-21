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

########################################################################
# A "one stop" place to pick up most common scribble imports.
#   Note: explicitly export symbols so Flake and Black don't mess things up.
#########################################################################
from scribble.document import document
from scribble.exceptions import DocumentException
from scribble.objdict import Objdict, INVALID
from scribble.scope import Element, QueryStream, primary_type, Query
from scribble.section import (
    Section,
    Text,
    StringTemplate,
    Snippet,
    PairedTemplate,
    text,
)
from scribble.table import Table, HeaderCell
from scribble.template import hex_addr
from scribble.template import template
from scribble.util import consistent_values, plus1, minus1, n_bytes
from scribble.diagrams import Figure, Image
from scribble.path_interpolation import pathLookup

__all__ = [
    "Section",
    "Text",
    "StringTemplate",
    "Snippet",
    "PairedTemplate",
    "text",
    "template",
    "document",
    "Element",
    "primary_type",
    "QueryStream",
    "Query",
    "Objdict",
    "INVALID",
    "Element",
    "DocumentException",
    "consistent_values",
    "plus1",
    "minus1",
    "Table",
    "HeaderCell",
    "n_bytes",
    "hex_addr",
    "Figure",
    "Image",
    "pathLookup",
]
