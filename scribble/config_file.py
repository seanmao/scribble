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

import json
import os
import yaml
from pathlib import Path


def read(filename: str) -> any:
    """
    Parse a configuration file, either yaml or json.
    If extension isn't specified, will check to see which one exists.
    :param filename: name of file, possibly without extension
    :return:  structured object or None
    """

    # If the file doesn't exist, try adding .yaml or .json to the file name.
    if os.path.isfile(filename):
        path = filename
    elif os.path.isfile(f"{filename}.yaml"):
        path = f"{filename}.yaml"
    elif os.path.isfile(f"{filename}.json"):
        path = f"{filename}.json"
    else:
        raise FileNotFoundError(
            f"Unable to find any of these configuration files:\n  "
            f"{filename}\n  {filename}.yaml\n  {filename}.json"
        )

    # Open the file and parse the contents.
    #   The json library parses json *much* faster than the yaml library,
    #   so use the json library if appropriate.
    if Path(path).suffix == ".json":
        obj = load_json(path)
    else:
        obj = load_yaml(path)

    # Return the configuration
    return obj


def load_yaml(name: str) -> any:
    with open(name, "r") as fp:
        obj = yaml.safe_load(fp)
    return obj


def load_json(name: str) -> any:
    with open(name, "r") as fp:
        obj = json.load(fp)
    return obj


def write(obj: any, filename: str):
    """
    Write a configuration file, either yaml or json.
    If extension isn't specified, will check to see which one exists.
    :param obj: the object to be saved in the config file.
    :param filename: name of file, possibly without extension
    """

    # Separate the file name from the extension
    name, extension = os.path.splitext(filename)

    # A common mistake is to use .yml instead of .yaml
    if extension == ".yml":
        extension = ".yaml"
        filename = name + extension

    # If not explicitly yaml or json, then add .yaml to the output name.
    if extension != ".yaml" and extension != ".json":
        extension = ".yaml"
        filename = filename + extension

    # save the object as requested.
    if extension == ".yaml":
        save_yaml(obj, filename)
    else:
        save_json(obj, filename)


def save_json(obj: any, name: str):
    with open(name, "w") as fp:
        json.dump(obj, fp)


def save_yaml(obj: any, name: str):
    with open(name, "w") as fp:
        yaml.safe_dump(obj, fp)
