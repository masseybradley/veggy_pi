#!/usr/bin/env python

from django.utils.translation import ugettext_lazy as _


def is_number(num):
    """
    """
    try:
        n = float(num)
    except ValueError:
        return False
    return True


def all_numbers(*numbers):
    """
    """
    for num in numbers:
        if not is_number(num):
            return False
    return True


def is_greater_than(max_val, min_val):
    if min_val > max_val or min_val == max_val:
        raise ValueError(_('%s must not be greater than %s' % (min_val, max_val))) 
        

def value_in_range(val, max_range):
    if val not in max_range:
        raise ValueError(_('%s must be in range %s' % (val, max_range)))


