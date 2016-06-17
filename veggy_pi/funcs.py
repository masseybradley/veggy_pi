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


def list_val_to_int(bit_list=None):
    if not bit_list:
        raise ValueError(u'no list provided in function call.')

    bit_list = [ int(x) for x in bit_list ]
    return bit_list


def shift_bit_list(bit_list=None):
    # takes a list of bits and for each bit shifts and returns an integer value
    if not bit_list:
        raise ValueError(u'no list provided to function call.')

    out = 0 
    for bit in bit_list:
        out = (out << 1) | bit 
    return out
