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

"""
A component that renders a simple table.
"""

import enum
import itertools
import typing as t

from scribble.obj import get_path
from scribble.template import template_string


class HAlign(enum.Enum):
    """Horizontal alignment."""

    LEFT = "<"
    CENTER = "^"
    RIGHT = ">"


class VAlign(enum.Enum):
    """Vertical alignment."""

    TOP = "<"
    MIDDLE = "^"
    BOTTOM = ">"


class Style(enum.Enum):
    """Table/Column/Cell styles.

    See http://www.methods.co.nz/asciidoc/chunked/ch23.html#X71

    Note: The DEFAULT style is not the same as not explicitly setting a style
    at all because by default a cell inherits its style from its column's style
    or the table's style. Explicitly setting the DEFAULT style will override an
    inherited style.
    """

    DEFAULT = "d"
    EMPHASIS = "e"
    MONOSPACED = "m"
    STRONG = "s"
    HEADER = "h"
    ASCIIDOC = "a"
    LITERAL = "l"
    VERSE = "v"


class Cell(t.NamedTuple):
    contents: str
    # See http://www.methods.co.nz/asciidoc/chunked/ch23.html#X84 for a
    # description of cell specifiers.
    col_span: int = 1
    row_span: int = 1
    halign: t.Optional[HAlign] = None
    valign: t.Optional[VAlign] = None
    style: t.Optional[Style] = None

    def __str__(self):
        return self.render()

    def render(self) -> str:
        return f"{self._specifiers}|{self.contents}"

    @property
    def _specifiers(self) -> str:
        col_str = f"{self.col_span}" if self.col_span != 1 else ""
        row_str = f".{self.row_span}" if self.row_span != 1 else ""
        span_str = f"{col_str}{row_str}+" if col_str or row_str else ""

        halign_str = f"{self.halign.value}" if self.halign else ""
        valign_str = f".{self.valign.value}" if self.valign else ""
        align_str = f"{halign_str}{valign_str}"

        style_str = f"{self.style.value}" if self.style else ""

        return f"{span_str}{align_str}{style_str}"


class HeaderCell(t.NamedTuple):
    name: str
    # See http://www.methods.co.nz/asciidoc/chunked/ch23.html#X70 for a
    # description of column specifiers.
    halign: t.Optional[HAlign] = None
    valign: t.Optional[VAlign] = None
    width: t.Optional[t.Union[str, int]] = None
    style: t.Optional[Style] = None

    @property
    def specifier_str(self) -> str:
        halign_str = f"{self.halign.value}" if self.halign else ""
        valign_str = f".{self.valign.value}" if self.valign else ""
        align_str = f"{halign_str}{valign_str}"

        width_str = f"{self.width}" if self.width else ""

        style_str = f"{self.style.value}" if self.style else ""

        return f"{align_str}{width_str}{style_str}"


CellLike = t.Union[Cell, str]


class Row:
    def __init__(self, cells: t.List[CellLike]) -> None:
        self.cells = [Cell(cell) if isinstance(cell, str) else cell for cell in cells]

    def __str__(self):
        return self.render()

    def render(self) -> str:
        return "\n".join(cell.render() for cell in self.cells)


RowLike = t.Union[Row, t.List[CellLike]]


class Table:
    def __init__(
        self,
        rows: t.List[RowLike],
        header: t.Optional[t.List[HeaderCell]] = None,
        title: t.Optional[str] = None,
        reference_id: t.Optional[str] = None,  # ID used for cross references
        autowidth: bool = False,
        roles: t.Optional[t.List[str]] = None,
    ) -> None:
        self.header = header
        self.rows = [row if isinstance(row, Row) else Row(row) for row in rows]
        self.title = title
        self.reference_id = reference_id
        self._validate_num_columns()
        self.autowidth = autowidth
        self.roles = roles or []

    def _get_num_columns(self) -> int:
        return (
            len(self.header)
            if self.header
            else sum(cell.col_span for cell in self.rows[0].cells)
        )

    def _validate_num_columns(self):
        """
        Check that all rows have the same number of columns.

        Takes into account row and column spans.
        """
        num_columns = self._get_num_columns()

        class ExtantSpan(t.NamedTuple):
            """
            A cell from a previous row that continues to span into future rows.
            """

            row_span: int
            col_span: int

        extant_spans = []
        for row in self.rows:
            total_columns = sum(cell.col_span for cell in row.cells) + sum(
                span.col_span for span in extant_spans
            )
            if total_columns != num_columns:
                raise ValueError(
                    f"All rows must have the same number of columns: "
                    f"{total_columns} != {num_columns} in row:\n{row}"
                )
            new_spans = [
                ExtantSpan(row_span=cell.row_span, col_span=cell.col_span)
                for cell in row.cells
                if cell.row_span != 1
            ]
            extant_spans = [
                span._replace(row_span=span.row_span - 1)
                for span in itertools.chain(extant_spans, new_spans)
                if span.row_span > 1
            ]

    @property
    def _properties(self):
        properties = {}
        if self.header:
            properties.update(
                {
                    "cols": ",".join([cell.specifier_str for cell in self.header]),
                    "options": "header",
                }
            )
        else:
            properties["cols"] = ",".join([""] * self._get_num_columns())
        autowidth = "%autowidth" if self.autowidth else ""
        roles = "".join([f".{role}" for role in self.roles])
        items = filter(
            None,
            [f"{autowidth}{roles}"]
            + [
                '{key}="{value}"'.format(key=key, value=value)
                for key, value in properties.items()
            ],
        )
        return "[{contents}]".format(contents=",".join(items))

    def __str__(self) -> str:
        return self.render()

    def render(self) -> str:
        template = """\
{%- if reference_id %}
[[{{ reference_id }}]]
{%- endif %}
{%- if title %}
.{{ title }}
{%- endif %}
{{ properties }}
|===
{% if header %}{% for header_cell in header %}^|{{ header_cell.name }} {% endfor %}{% endif %}
{%- for row in rows %}
{{ row }}
{% endfor %}
|===
"""
        string = template_string(
            template,
            reference_id=self.reference_id,
            title=self.title,
            properties=self._properties,
            header=self.header,
            rows=self.rows,
        )

        return string


def ObjectTable(
    objects: t.Iterable[dict],
    field_names: t.List[str],
    header: t.Optional[t.List[HeaderCell]] = None,
    title: t.Optional[str] = None,
    reference_id: t.Optional[str] = None,  # ID used for cross references
    autowidth: bool = False,
    roles: t.Optional[t.List[str]] = None,
) -> Table:
    """
    Build a table from a sequence of dictionary-like objects, given field names for each column.
    """
    # For each object, create a list of strings with the corresponding fields.
    #  TODO: treat "null" as a blank field.
    strings = [[getValue(obj, path) for path in field_names] for obj in objects]

    # Build a table from the object's values
    return Table(strings, header, title, reference_id, autowidth, roles)


def getValue(obj, key) -> str:
    if isinstance(key, str):
        v = get_path(obj, key)
    else:
        v = key(obj)
    return str(v)
