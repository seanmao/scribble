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

from contextlib import suppress
from os.path import dirname
from scribble.scope import Element
from scribble.importer import LoadSourceFile
from scribble.obj import scan, set_path
from scribble.path_interpolation import pathLookup
from scribble.section import load_section

# *********************************************
# Fixups are things which "fix things up".
#    They are associated with
#         1) the specific document
#         2) the type of document
#         3) individual design elements  (snippets)
#
# Fixup files take two forms:
#   - Python file "Fixup.py"
#     Contains a Fixup(element, document) function which can alter the design element.
#     ("document" is available in case the fixup needs broader knowledge about the document)
#   - Yaml file "Fixup.yaml"
#     Contains a list of Path:Value patches, stating where each value is patched in.
#
# Note there can be both Python and Yaml files.
#   Python functions are applied first, then the yaml patches
#
# It is possible for a fixup to add or remove sub-elements, changing the shape of the design tree.
#   Fixups must be applied in a top-down manner.   document -->  design --> individual elements
#


def fixup_document(document: Element):
    """
    Apply fixups to an entire document.

    Determining the proper order to apply fixups has been a challenge.
    Originally, wanted specific document to override document type to override snippets, so
    we applied them  snippets --> design --> our specific document.

    However, we had to change the order.
      - some fixups are "unfixable" (wrong shape or wrong element types)
        unless they are applied from the document level. These document fixups must be
        applied before all other fixups. They are based on "document type".
      - With fixup functions, high level fixups can impact lower level fixups,
        so we need to apply the design fixups before the snippet fixups.
      - The fixups can alter the shape of the design tree, so they have to be applied in
        top down manner.

    As a result, we now apply fixups: document type --> design --> snippets (top down).

    Both orderings have merit, so we may have to revisit, especially after the "unfixable"
    errors get fixed.
    """

    # Apply Document Type fixups from directories of the document generator modules
    for module in document.document_sections:
        apply_fixup_function(document, document, find_section_directory(module))
        apply_fixup_patches(document, document, find_section_directory(module))

    # Apply Design fixups from the same directory as the document config file
    if document.design_file:
        apply_fixup_function(
            document.design, document, pathLookup("{design}", document.config_file)
        )
        apply_fixup_patches(
            document.design, document, pathLookup("{design}", document.config_file)
        )

    # Apply Element (snippet) to each matching element of the design.
    if document.snippets and document.design:
        scan(document.design, lambda element: fixup_snippet(element, document))


def fixup_snippet(element: Element, document: Element):
    """
    Apply fixups to a snippet. Start with most general type and finish with most specific.
    """
    if element._types:
        for typ in reversed(element._types):
            for dir in document.snippets:
                fixup_element(element, document, f"{dir}/components/{typ}")


def fixup_element(element: Element, document: Element, dir: str):
    """
    Fixup a specific element, function first then the patch.
    """
    apply_fixup_function(element, document, dir)
    apply_fixup_patches(element, document, dir)


def apply_fixup_patches(element: Element, document: Element, dir: str):
    """
    Apply Fixup.yaml patches to an element.
    """
    # Get the Fixup.yaml file if there is one.
    with suppress(FileNotFoundError):
        patches = Element.read(f"{dir}/Fixup")
        if patches:
            apply_patches(element, patches)


def apply_patches(element: Element, patches: dict):

    # Apply each of the corrections.
    for path, value in patches.items():
        set_path(element, path, value)


def apply_fixup_function(element: Element, document: Element, dir: str):
    """
    Apply Fixup.py function to an element.
    """

    # Create a dummy module name so we don't have name conflicts when we load Fixup.py
    dummy_name = f"Fixup.Fix_{dir.replace('/', '_')}"

    # If it exists, apply the fixup function.
    fixup = LoadSourceFile("Fixup", dummy_name, f"{dir}/Fixup.py")
    if fixup:
        fixup(element, document)


def find_section_directory(modulePath: str) -> str:
    """
    Here is the situation:
      - Want to have errata specific to a type of document
      - The type of document is specified as a high level python module, not as a file.
      - We know the module name, but which directory should we use for the errata?
    """

    # Lookup the module which has that name and function. Verifies the function exists.
    _, module = load_section(modulePath)  # refactor load_section so it doesn't take scope.

    # Return the directory name of the module
    dir = dirname(module.__file__)
    return dir
