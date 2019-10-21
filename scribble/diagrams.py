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

import html
from typing import List, Union
from pathlib import Path
from base64 import b64encode
import subprocess
import json
from scribble.exceptions import DocumentException
from scribble.section import Text, text
from scribble.path_interpolation import pathLookup


@text
def Figure(
    img: Union[str, bytes], *, suffix="", title="", id="", width="", **kwargs
) -> Text:
    """
    Include an image file or image bytes in the document.
    This routine "hides" a bunch of details
      - is the image inlined?
      - how are the title and id formatted?
      - sets the width if requested
    """
    # Generate title and reference ids if requested.
    if id:
        yield f"[[{id}]]\n"
    if title:
        yield f".{title}\n"

    # Generate the asciidoc image call.
    yield from Image(img, alt=title, width=width, suffix=suffix, **kwargs)


def Image(img: Union[str, bytes], *, alt="", width="", suffix="", **kwargs) -> Text:
    """
    A document section consisting solely if an image.
    """
    # Create a data source url from the image data
    if isinstance(img, str):
        src = dataURL(img, **kwargs)
    elif isinstance(img, bytes) and suffix:
        src = dataUrlFromBytes(img, suffix)
    else:
        raise DocumentException(
            f"Image - must pass file name or bytes+suffix  id={id} alt={alt}"
        )

    # Create the asciidoc "image::...." with an optional width.
    w = f", width={width}" if width else ""  # optional width
    img = f"image::{src}[{alt}{w}]"
    return Text(img)


def dataURL(file: str, _file_=None, **kwargs) -> str:
    """
    Convert an image file into an inlined data url.
    """
    path = Path(pathLookup(file, _file_))
    if not path.exists():
        raise DocumentException(f"Image file {file} can't be found")

    return dataUrlFromBytes(path.read_bytes(), path.suffix)


mimeHeader = {".svg": "svg+xml;base64", ".png": "png;base64"}


def dataUrlFromBytes(img: bytes, suffix: str) -> str:
    """
    Convert a sequence of image bytes into an inlined data url
    """
    if suffix not in mimeHeader:
        raise DocumentException("embedImg: Unable to embed images of type {type")

    src = f"data:image/{mimeHeader[suffix]},{base64(img)}"
    return src


def base64(b: bytes) -> str:
    """
    Convert a sequence of bytes into a base64 string
    """
    b64 = b64encode(b)
    s = b64.decode()  # as a string
    return s


# ###################
#
# The following routines run an external program, sending it data via stdin and reading back stdout.
#   They are contained in Diagrams.py because they are only used for generating diagrams.
#   When others have need for them, they should be refactored to a different
#   scribble/xxx source file.
#
# ###################


def pipe_json_to_str(cmd: List[str], **params) -> str:
    """
    Run an external command, passing it json and reading back characters.
    """
    return pipe_json_to_bytes(cmd, **params).decode()


def pipe_json_to_bytes(cmd: List[str], **params) -> bytes:
    """
    Run an external command, passing it JSON and returning binary bytes.
    """
    return pipe(cmd, toJSON(params).encode())


def pipe(cmd: List[str], input: bytes) -> bytes:
    """
    Run an external command, passing it bytes and returning bytes.
    """
    result = subprocess.run(args=cmd, input=input, check=True, stdout=subprocess.PIPE)
    output = result.stdout
    return output


def toJSON(obj) -> str:
    # Convert HTML escapes to unicode before sending.
    return html.unescape(json.dumps(obj))


def fromJSON(data: str) -> any:
    return json.loads(data)
