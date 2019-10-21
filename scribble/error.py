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

import logging
from functools import wraps
from typing import Optional

"""

Error handling.

At the moment, scribble does almost no error handling, allowing the process to terminate
with an exception. Harsh as it seems, this is probably the preferred method of handling
errors in Scribble for now.

In the longer term, we may need to actually recover from errors. There are several
ways of doing error recovery, some more "Pythonic" or "Functional" than others.

1) Raise and catch exception handling.
   This approach is common in Python and Java, but it can lead to
   complicated and difficult to understand code. It is very difficult
   to debug or to know which exceptions might occur when exceptions are widespread
   throughout a large project.
2) Functional writer monad. A common approach in Scala is to return a "Try" object
   which contains either the desired value (payload) or an error message. Scala's
   "Try" is nice because it also catches exceptions from non-functional low level code.
3) Optional. In this method, a function returns either the expected value, or
   it returns a special sentinal value "None".  Error messages are passed through
   a side channel, typically an error log file. Optional is a common compromise in languages
   which don't support the "functional" concepts.

If we decide to extend Scribble to do error recovery, the Optional compromise  is probably the
most practical solution. It maintains a clear flow of execution, avoiding the problems
of "try catch" statements scattered throughout a large body of code.

The issue is, in the future, how do we get from our current "raise exception and die"
to "log the error and return None" error handling?

Conveniently, Python supports function wrappers called "decorators". By placing a decorator
in front of a "raise and die" function, we convert it to "log message and return None".
When we feel like it, we can recode the function more elegantly, but in the meantime
we have a quick and easy conversion to Optional.

So, this file contains two main routines for handling errors.

   1) error("message") -  logs the message and returns None, the two
                          essential features of Optional error handling.

   2) @exception_None   - tranforms an exception throwing function into an Optional function.


To put things in perspective, these routines are more plans for the future rather than routines for
immediate use. They show we have a convenient way to introduce Optional error handling
when the need arises. For now, we can be comfortable with "raise and die".

"""


def error(msg: Optional[str] = None) -> None:
    """
    A shorthand routine to propagate None up the call tree while logging a message.

    It helps with a common coding pattern.
       if (do_something() is None)
           return error("Couldn't do something")
    """
    if msg is not None:
        log_error(msg)
    return None


def exception_None(f):
    """
    Function decorator which catches an exception, logs it, and returns None.
    Composes decorator @exception_value with @exception_log
    """
    return exception_value(None)(exception_log(f))


"""
The following are helper functions used to implement the two main ones.
   They may be useful in their own right.
"""


def log_error(msg: str):
    """
    A wrapper function to log an error using your favorite logger.
    It consolidates error messages through a common function,
    possibly adding timestamps, user names or whatever is desired.
    This one is just a stub. Pick favorite error logger and use it here.
    """
    logging.error(msg)


def exception_value(value):
    """
    Function decorator to catch exceptions and return a default value.
    :param value: the value to return when an exception is raised.

    Use
       @exception_value(None)
       def method(self, arg1,  arg2 ...)

    if method has an uncaught exception, it returns None

    Apologies for the function returns a function which returns a function.
    Go online and read up on Python decorators. At least the code is short.

    TODO: To maintain type correctness, the type attribute of the return value
         should be updated to be Either(value type, original type).

    """

    def decorator(f):
        @wraps(f)  # Should update return type to be Either.
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception:
                return value

        return wrapper

    return decorator


def exception_log(f):
    """
    Function decorator to log an exception before passing it on.

    Use
        @exception_log
        def method(self, arg1, ...).
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error(f"Caught Exception: {e}")
            raise e

    return wrapper
