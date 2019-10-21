# See LICENSE.django for license details.


# Adapted from Django 2.0.2
# A few lines were changed in order to make invalid input cause exceptions to
# be raised rather than silenced.
# https://github.com/django/django/blob/2.0.2/django/template/defaultfilters.py#L847
def pluralize(value, arg="s"):
    """
    Return a plural suffix if the value is not 1. By default, use 's' as the
    suffix:

    * If value is 0, vote{{ value|pluralize }} display "0 votes".
    * If value is 1, vote{{ value|pluralize }} display "1 vote".
    * If value is 2, vote{{ value|pluralize }} display "2 votes".

    If an argument is provided, use that string instead:

    * If value is 0, class{{ value|pluralize:"es" }} display "0 classes".
    * If value is 1, class{{ value|pluralize:"es" }} display "1 class".
    * If value is 2, class{{ value|pluralize:"es" }} display "2 classes".

    If the provided argument contains a comma, use the text before the comma
    for the singular case and the text after the comma for the plural case:

    * If value is 0, cand{{ value|pluralize:"y,ies" }} display "0 candies".
    * If value is 1, cand{{ value|pluralize:"y,ies" }} display "1 candy".
    * If value is 2, cand{{ value|pluralize:"y,ies" }} display "2 candies".
    """
    if "," not in arg:
        arg = "," + arg
    bits = arg.split(",")
    if len(bits) > 2:
        return ""
    singular_suffix, plural_suffix = bits[:2]

    try:
        if float(value) != 1:
            return plural_suffix
    except TypeError:  # Value isn't a string or a number; maybe it's a list?
        if len(value) != 1:
            return plural_suffix
    return singular_suffix


# Adapted from Django 2.0.2
# A few lines were changed in order to remove a dependency on Django
# translation utility functions by removing default arguments.
# https://github.com/django/django/blob/2.0.2/django/template/defaultfilters.py#L767
def yesno(value, arg):
    """
    Given a string mapping values for true, false, and (optionally) None,
    return one of those strings according to the value:
    ==========  ======================  ==================================
    Value       Argument                Outputs
    ==========  ======================  ==================================
    ``True``    ``"yeah,no,maybe"``     ``yeah``
    ``False``   ``"yeah,no,maybe"``     ``no``
    ``None``    ``"yeah,no,maybe"``     ``maybe``
    ``None``    ``"yeah,no"``           ``"no"`` (converts None to False
                                        if no mapping for None is given.
    ==========  ======================  ==================================
    """
    bits = arg.split(",")
    if len(bits) < 2:
        return value  # Invalid arg.
    try:
        yes, no, maybe = bits
    except ValueError:
        # Unpack list of wrong size (no "maybe" value provided).
        yes, no, maybe = bits[0], bits[1], bits[1]
    if value is None:
        return maybe
    if value:
        return yes
    return no
