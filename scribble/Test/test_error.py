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

from scribble.error import error
from scribble.error import exception_None
from scribble.error import exception_log
from scribble.error import exception_value

'''
# TODO: Mocks are not quite working. Comment out for now.

#############################
# Set up a mock version of logging.error
#  For testing, rather than writing to an error log,
#  we'll stash the message in a global variable.
#  Calling "get_message()" will fetch and reset the message.
###############################

import logging
import unittest.mock as mock

message = None


def logging_error(*args, **kwargs):
    global message
    message = "EXCEPTION"


def get_message():
    global message
    msg = message
    message = None
    return msg


@mock.patch('newscribble.error.logging', side_effect=logging_error)
def test_mock():
    """
    verify mock "logging.error" is in place and returns/resets the message.
    """

    assert(get_message() is None)
    error("ERROR")
    assert(get_message() == "ERROR")
    assert(get_message() is None)

'''


# Dummy exception to use for testing.
class ExceptionTest(Exception):
    pass


def test_error():
    # Verify error() returns None and does not log a message
    value = error()
    assert value is None, "error() returns None"
    # assert get_message() is None, "no error message logged" // uses mock, which isn't working.

    # Verify error(msg) returns None and logs a message
    val = error("Error Message")
    assert val is None, "error(msg) returns None"
    # assert get_message() == "Error Message", "message was logged" // mock isn't working


def test_exception_value():
    # Verify @exception_value returns function value normally.
    @exception_value("EXCEPTION")
    def id(x):
        return x

    assert id("ACTUAL") == "ACTUAL"

    # Verify @exception_value catches the exception and eturns the value
    @exception_value("EXCEPTION")
    def exception():
        raise ExceptionTest("exception_value_test")

    value = exception()
    assert value == "EXCEPTION", "Should return value on exception"


def test_exception_log():
    # Verify @exception_log returns normal value
    @exception_log
    def id(x):
        return x

    assert id("VALUE") == "VALUE"

    # Verify @exception_log logs the exception and passes it on
    @exception_log
    def exception():
        raise ExceptionTest("EXCEPTION")

    try:
        exception()
        assert False, "Failed to raise exception"
    except ExceptionTest as e:
        assert f"{e}" == "EXCEPTION", "Returned wrong exception value"
        # assert get_message() == "EXCEPTION", "Failed to log correct message"


def test_exception_None():
    @exception_None
    def id(x):
        return x

    assert id("VALUE") == "VALUE"

    # verify @exception_None catches exception, logs it, and returns None
    @exception_None
    def exception():
        raise ExceptionTest("EXCEPTION")

    value = exception()
    assert value is None, "Should return None"
    # assert get_message() == "EXCEPTION", "Should log the exception string"
