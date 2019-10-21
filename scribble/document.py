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

from typing import List
from os.path import dirname
import sys
from pathlib import Path
import scribble.template as template
from scribble.exceptions import DocumentException
from scribble.importer import JinjaFileLoader, addImportPath
from scribble.scope import Element, MemoizedQueryStream
from scribble.section import Section, Snippet
from scribble.fixup import fixup_document
from scribble.diagrams import Figure, Image
import argparse
from scribble.path_interpolation import initPathInterpolation, pathLookup


def document(
    *,
    config: str = "",
    output: str,
    design_file: str = "",
    sections: List[str] = None,
    directories: List[str] = None,
    values: List[str] = None,
):
    """
    Create a document.
    It reads a config file which tells it where to fetch design data and which sections to process,
    and creates an asciidoc output file.

    :param config: Name of the document's configuration file
    :param output_file:  Name of the .adoc file to create
    :param design_file: Name of the object model design file
    :param sections: A list of document section to add to the configuration.
    :param directories: A list of snippet directories to add to the configuration.
    :param values: A list of "path=value" strings to update the document
    """

    # Default the following parameters to empty list
    sections = sections or []
    directories = directories or []
    values = values or []

    # Read the configuration and prepare to create a document.
    doc = setup(config, output, design_file, sections, directories, values)

    # Pass globals as context to all subsequent sections
    context = doc.globals if doc.globals else {}

    # Open the output file for writing.
    with open(pathLookup(doc.output_name), "w") as f:

        # For each of the requested sections
        for section in doc.document_sections:

            # Process the section and save the output.
            for text in Section(section, doc, **context):
                f.write(str(text))


def setup(
    config: str,
    output: str,
    design_file: str,
    sections: List[str],
    directories: List[str],
    values: List[str],
):
    """
    Read in the document and design data needed to create a document.
    """
    # Read in the document configuration (or start from scratch)
    if config:
        doc = Element.read(config)  # config cannot have interpolations.
        doc.config = config
    else:
        doc = Element()

    # Update high level document fields if passed in command line.
    if design_file:
        doc.design_file = design_file
    if output:
        doc.output_name = output

    # Merge document sections and snippets from both the command line and the configuration
    doc.document_sections = [*sections, *doc.document_sections]
    doc.directories = [*directories, *doc.directories]

    # We should not have both a design and a design file
    if doc.design and doc.design_file:
        raise DocumentException(
            f"The document should not have both a design and a design file {doc.design_file}."
        )

    # We must have at least one document section
    if not doc.document_sections:
        raise DocumentException("The document must have at least one document-section")

    # Apply the command line values to the document. These override any values in the config.
    for assignment in values:
        [path, value] = assignment.split("=", 1)
        doc.set_path(path, value)

    # Set up interpolations for this document. Process {here} immediately.
    def dir(name):
        return name and dirname(name)

    initPathInterpolation(
        dir(doc.config) or "",
        config=dir(doc.config) or "",
        design=dir(doc.design_file) or "",
        output=dir(doc.output_name) or "",
        **(doc.paths or {}),
    )

    # Read in the design file (if present)
    if doc.design_file:
        doc.design = Element.read(pathLookup(doc.design_file, doc.config))

    # Add the additional document directories to sys.path so we can find sections.
    if doc.directories:
        directories = [
            pathLookup(directory, doc.config) for directory in doc.directories
        ]
        addImportPath(*directories)

    # Keep track of which directories contain component snippets. Mainly to help with Fixups.
    doc.snippets = [path for path in sys.path if Path(f"{path}/components").is_dir()]

    # Prepare to load jinja2 templates as Python modules.
    JinjaFileLoader.install()

    # Add some necessary procedures so templates can access them.
    template.GLOBALS.update(
        Section=Section, Snippet=Snippet, Figure=Figure, Image=Image
    )

    # Apply fixups to the document.
    fixup_document(doc)

    # Finished. Our design/document tree is set up. No more changes to the design tree.
    #  We can "memoize" future queries against the tree.
    MemoizedQueryStream.enable()
    return doc


def main() -> None:
    """
    Generate an Asciidoc document.
       Python3.7  -m scribble.document
         --output   <name of asciidoc output file>
         --config   <name of document configuration file>
         --sections <list of main document sections>
         --design-file <name of object model design file>
         --snippets <list of directories where snippets are found>
         --values  <list of path=value pairs to be inserted into the document>

    The command line arguments are merged into the document configuration.
      - document "sections" are appended together
      - "directories" directories are appended together
      - values are inserted into the document at their corresponding locations

    In the extreme case, it is possible to create a document with no document configuration file.
    All the settings with string values can come from the command line.
    """
    # Fetch the program arguments.
    args = parse_args()

    # Build the document
    document(
        config=args.config,
        output=args.output,
        sections=args.sections,
        directories=args.directories,
        design_file=args.design_file,
        values=args.values,
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate an Asciidoc document from scribble Templates"
    )
    parser.add_argument("--config", help="File describing the document, .yaml or .json")
    parser.add_argument(
        "--output", help="Name of the asciidoc output file", required=True
    )
    parser.add_argument(
        "--sections",
        help="One or more Python modules which generate the document.",
        nargs="*",
        default=[],
    )
    parser.add_argument(
        "--directories",
        help="One or more directories which contain document generators",
        nargs="*",
        default=[],
    )
    parser.add_argument("--design-file", help="Name of the Object Model design file")
    parser.add_argument(
        "--values",
        help="Followed by a list of path=value strings to be inserted into the document",
        nargs="*",
        default=[],
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
